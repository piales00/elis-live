import argparse
import hashlib
import io
import json
import os
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import duckdb
import joblib
import numpy as np
import pandas as pd
from shapely import contains_xy
from shapely.geometry import shape

import config


MODEL_NAME = "emulator.joblib"
MASK_NAME = "static_mask.json"
CELL_REGIONS_NAME = "cell_regions.json"
CALIBRATION_NAME = "calibration.json"
SCOREBOARD_NAME = "scoreboard.json"
PREDICTIONS_DIR = "predictions"
FEATURES = ["n_points", "frp_sum", "frp_max", "bright_max", "scan_mean",
            "track_mean", "has_day", "has_night", "month_sin", "month_cos", "region"]
CSV_COLUMNS = ("latitude", "longitude", "acq_date", "acq_time", "satellite", "confidence",
               "frp", "scan", "track", "daynight", "brightness", "bright_ti4")
TAILS = ((1 - config.CI_LEVEL) / 2, (1 + config.CI_LEVEL) / 2)
UNIT = "fire cell-days"


def connect():
    return duckdb.connect(config={"autoinstall_known_extensions": "false",
                                  "autoload_known_extensions": "false"})


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def seal(value):
    body = {key: item for key, item in value.items() if key != "sha256"}
    return dict(body, sha256=sha256_bytes(canonical(body).encode()))


def verify(value):
    return seal(value)["sha256"] == value.get("sha256")


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n")


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def download(source, day):
    key = os.environ.get("FIRMS_MAP_KEY", "").strip()
    if not key:
        raise SystemExit("FIRMS_MAP_KEY is not set; pass --csv to use a local FIRMS file.")
    bbox = ",".join(str(value) for value in config.PERU_BBOX)
    url = config.FIRMS_AREA_URL.format(key=key, source=config.LIVE_SOURCES[source]["firms"],
                                       bbox=bbox, date=day.isoformat())
    try:
        with urllib.request.urlopen(url, timeout=config.FIRMS_TIMEOUT_SECONDS) as response:
            data = response.read()
    except urllib.error.HTTPError as error:
        raise SystemExit(f"FIRMS request for {config.LIVE_SOURCES[source]['firms']} failed with HTTP {error.code}.") from None
    except urllib.error.URLError as error:
        raise SystemExit(f"FIRMS request for {config.LIVE_SOURCES[source]['firms']} failed: {error.reason}.") from None
    if not data.lstrip().lower().startswith(b"latitude"):
        raise SystemExit(f"FIRMS returned an unexpected response for {config.LIVE_SOURCES[source]['firms']}: "
                         f"{data[:80].decode(errors='replace').strip()!r}")
    return data


def read_firms(data):
    frame = pd.read_csv(io.BytesIO(data), dtype=str, keep_default_na=False) if data.strip() else pd.DataFrame()
    for column in CSV_COLUMNS:
        if column not in frame:
            frame[column] = ""
    return frame[list(CSV_COLUMNS)].fillna("")


def peru_polygon():
    regions = json.loads((config.PROCESSED_DIR / "regions.geojson").read_text())
    feature = next(f for f in regions["features"] if f["properties"]["id"] == config.NATIONAL)
    return shape(feature["geometry"]).buffer(config.PERU_POINT_BUFFER_DEG)


def load_static_mask(live_dir):
    interim = config.INTERIM_DIR / "static_mask.parquet"
    if interim.is_file():
        with connect() as con:
            rows = con.execute("SELECT instrument, cell_y, cell_x FROM read_parquet(?)", [str(interim)]).fetchall()
        return {(i, int(y), int(x)) for i, y, x in rows}
    value = json.loads((live_dir / MASK_NAME).read_text())
    return {(row["instrument"], row["cell_y"], row["cell_x"]) for row in value["cells"]}


def load_cell_regions(live_dir):
    path = live_dir / CELL_REGIONS_NAME
    if not path.is_file():
        return {}
    return {(y, x): region for y, x, region in json.loads(path.read_text())["cells"]}


def assign_unseen(cells):
    from regions import assign_regions

    with connect() as con:
        con.register("unseen_cells", cells[["cell_y", "cell_x"]].drop_duplicates())
        con.execute("CREATE TEMP TABLE unseen AS SELECT cell_y::INTEGER AS cell_y, cell_x::INTEGER AS cell_x FROM unseen_cells")
        assign_regions(con, "unseen")
        rows = con.execute("SELECT cell_y, cell_x, region FROM unseen").fetchall()
    return {(y, x): region for y, x, region in rows}


def build_cells(raw, source, day, live_dir):
    spec = config.LIVE_SOURCES[source]
    frame = raw[raw.satellite.isin(spec["satellites"]) & (raw.acq_date == day.isoformat())].copy()
    if spec["instrument"] == "viirs":
        frame = frame[frame.confidence.str.lower().isin(config.VIIRS_CONFIDENCE)]
        frame["brightness"] = frame.bright_ti4.where(frame.bright_ti4 != "", frame.brightness)
    else:
        frame = frame[pd.to_numeric(frame.confidence, errors="coerce") >= config.MODIS_MIN_CONFIDENCE]
    for column in ("latitude", "longitude", "frp", "scan", "track", "brightness"):
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame = frame[contains_xy(peru_polygon(), frame.longitude.to_numpy(), frame.latitude.to_numpy())]
    frame["cell_y"] = np.floor(frame.latitude / config.GRID_DEG).astype(int)
    frame["cell_x"] = np.floor(frame.longitude / config.GRID_DEG).astype(int)
    mask = load_static_mask(live_dir)
    frame = frame[np.array([(spec["instrument"], y, x) not in mask for y, x in zip(frame.cell_y, frame.cell_x)], dtype=bool)]
    detections = len(frame)
    with connect() as con:
        con.register("points", frame)
        cells = con.execute("""
            SELECT cell_y, cell_x, count(*) AS n_points, sum(frp ORDER BY frp) AS frp_sum,
                max(frp) AS frp_max, max(brightness) AS bright_max,
                avg(scan ORDER BY scan) AS scan_mean, avg(track ORDER BY track) AS track_mean,
                bool_or(daynight = 'D') AS has_day, bool_or(daynight = 'N') AS has_night
            FROM points GROUP BY cell_y, cell_x ORDER BY cell_y, cell_x
        """).df()
    lookup = load_cell_regions(live_dir)
    cells["region"] = [lookup.get((y, x)) for y, x in zip(cells.cell_y, cells.cell_x)]
    missing = cells.region.isna()
    if missing.any():
        assigned = assign_unseen(cells[missing])
        cells.loc[missing, "region"] = [assigned.get((y, x)) for y, x in zip(cells.cell_y[missing], cells.cell_x[missing])]
    cells = cells[cells.region.notna()].reset_index(drop=True)
    cells["date"] = day
    cells["month"] = day.month
    return cells, detections


def feature_frame(cells):
    x = cells.copy()
    x["month_sin"] = np.sin(2 * np.pi * x.month / 12)
    x["month_cos"] = np.cos(2 * np.pi * x.month / 12)
    x["region"] = pd.Categorical(x.region, categories=config.REGIONS)
    for column in ("has_day", "has_night"):
        x[column] = x[column].astype(bool)
    return x[FEATURES]


def emulate(bundle, cells):
    if cells.empty:
        return cells.assign(p=pd.Series(dtype=float), r=pd.Series(dtype=float))
    rates = {(row["region"], row["month"]): row["r"] for row in bundle["rates"]}
    probability = bundle["model"].predict_proba(feature_frame(cells))[:, 1]
    return cells.assign(p=probability, r=[rates[(region, month)] for region, month in zip(cells.region, cells.month)])


def regional_mu(scored):
    grouped = scored.groupby("region").agg(n=("p", "size"), sp=("p", "sum"), r=("r", "first"))
    return {region: (int(grouped.n.get(region, 0)),
                     float(grouped.sp.get(region, 0.0) + grouped.r.get(region, 0.0) * grouped.n.get(region, 0)))
            for region in config.REGIONS}


def predictive_draws(mu, drift, sigma, rng, draws):
    z = rng.standard_normal(draws)
    return rng.poisson(mu * drift * np.exp(sigma * z - sigma ** 2 / 2))


def interval(mu, drift, sigma, rng, draws=config.LIVE_DRAWS):
    values = predictive_draws(mu, drift, sigma, rng, draws)
    low, high = np.quantile(values, TAILS, method="inverted_cdf")
    return float(low), float(high)


def model_version(path):
    return "emulator-" + sha256_bytes(path.read_bytes())[:12]


def predict(day, live_dir, csv=None, source="auto", force=False):
    target = live_dir / PREDICTIONS_DIR / f"{day.isoformat()}.json"
    if target.is_file() and not force:
        raise SystemExit(f"A sealed prediction for {day.isoformat()} already exists; it is never overwritten.")
    bundle = joblib.load(live_dir / MODEL_NAME)
    calibration = json.loads((live_dir / CALIBRATION_NAME).read_text())
    candidates = ["snpp", "noaa20"] if source == "auto" else [source]
    for candidate in candidates:
        data = Path(csv).read_bytes() if csv else download(candidate, day)
        raw = read_firms(data)
        if source != "auto" or not raw[raw.satellite.isin(config.LIVE_SOURCES[candidate]["satellites"])].empty:
            break
    source = candidate
    cells, detections = build_cells(raw, source, day, live_dir)
    scored = emulate(bundle, cells)
    mu = regional_mu(scored)
    parameters = {row["region"]: row for row in calibration["sources"][source]["regions"]}
    rng = np.random.default_rng([config.SEED, day.toordinal()])
    rows = []
    national_mu = 0.0
    for region in config.REGIONS:
        n, value = mu[region]
        drift, sigma = parameters[region]["drift_factor"], parameters[region]["sigma"]
        low, high = interval(value, drift, sigma, rng)
        national_mu += value * drift
        rows.append({"region": region, "viirs_cell_days": n, "aqua_emulated": round(value, 2),
                     "aqua_predicted": round(value * drift, 2), "aqua_low": low, "aqua_high": high})
    national = parameters[config.NATIONAL]
    low, high = interval(national_mu, 1.0, national["sigma"], rng)
    rows.insert(0, {"region": config.NATIONAL, "viirs_cell_days": sum(mu[r][0] for r in config.REGIONS),
                    "aqua_emulated": round(sum(mu[r][1] for r in config.REGIONS), 2),
                    "aqua_predicted": round(national_mu, 2), "aqua_low": low, "aqua_high": high})
    prediction = {
        "date": day.isoformat(), "generated_at_utc": utc_now(), "unit": UNIT, "ci_level": config.CI_LEVEL,
        "viirs_source": source, "firms_source": config.LIVE_SOURCES[source]["firms"],
        "input_sha256": sha256_bytes(data), "viirs_detections": detections,
        "model_version": model_version(live_dir / MODEL_NAME),
        "calibration_sha256": sha256_bytes((live_dir / CALIBRATION_NAME).read_bytes()),
        "regions": rows,
        "method": ("Emulator probability that Aqua sees each VIIRS cell-day, summed, plus the Aqua-only residual rate; "
                   "multiplied by the recent drift factor; range from a Poisson-lognormal predictive distribution "
                   "whose spread was fitted on the calibration window."),
    }
    sealed = seal(prediction)
    write_json(target, sealed)
    return sealed


def empty_scoreboard():
    return {"unit": UNIT, "ci_level": config.CI_LEVEL, "updated_at_utc": None, "rows": [], "summary": []}


def summarize(rows):
    summary = []
    for region in (config.NATIONAL, *config.REGIONS):
        scored = [row for row in rows if row["region"] == region and row["observed"] is not None]
        if not scored:
            continue
        errors = np.array([row["error"] for row in scored], dtype=float)
        observed = np.array([row["observed"] for row in scored], dtype=float)
        summary.append({"region": region, "n_days": len(scored),
                        "coverage": round(float(np.mean([row["inside"] for row in scored])), 4),
                        "mean_error": round(float(errors.mean()), 2),
                        "mean_abs_error": round(float(np.abs(errors).mean()), 2),
                        "mean_abs_error_pct": round(float(np.abs(errors).sum() / observed.sum() * 100), 2) if observed.sum() else None})
    return summary


def score(day, live_dir, csv=None):
    path = live_dir / PREDICTIONS_DIR / f"{day.isoformat()}.json"
    if not path.is_file():
        raise SystemExit(f"No sealed prediction for {day.isoformat()}.")
    prediction = json.loads(path.read_text())
    if not verify(prediction):
        raise SystemExit(f"The prediction for {day.isoformat()} does not match its SHA-256 seal.")
    data = Path(csv).read_bytes() if csv else download("aqua", day)
    raw = read_firms(data)
    available = not raw[raw.satellite.isin(config.LIVE_SOURCES["aqua"]["satellites"])].empty
    cells, _ = build_cells(raw, "aqua", day, live_dir)
    counts = cells.groupby("region").size().to_dict()
    counts[config.NATIONAL] = len(cells)
    board_path = live_dir / SCOREBOARD_NAME
    board = json.loads(board_path.read_text()) if board_path.is_file() else empty_scoreboard()
    board["rows"] = [row for row in board["rows"] if row["date"] != day.isoformat()]
    for entry in prediction["regions"]:
        observed = int(counts.get(entry["region"], 0)) if available else None
        board["rows"].append({
            "date": day.isoformat(), "region": entry["region"], "viirs_source": prediction["viirs_source"],
            "predicted": entry["aqua_predicted"], "low": entry["aqua_low"], "high": entry["aqua_high"],
            "observed": observed,
            "inside": None if observed is None else bool(entry["aqua_low"] <= observed <= entry["aqua_high"]),
            "error": None if observed is None else round(observed - entry["aqua_predicted"], 2),
            "status": "scored" if available else "no_aqua_data",
            "prediction_sha256": prediction["sha256"], "prediction_generated_at_utc": prediction["generated_at_utc"],
            "aqua_input_sha256": sha256_bytes(data), "scored_at_utc": utc_now(),
        })
    board["rows"].sort(key=lambda row: (row["date"], (config.NATIONAL, *config.REGIONS).index(row["region"])))
    board["summary"] = summarize(board["rows"])
    board["updated_at_utc"] = utc_now()
    write_json(board_path, board)
    return board


def joint_days(start, end):
    excluded = [interval for source in (config.OUTAGES, config.DEGRADED)
                for sensor in ("aqua", "snpp") for interval in source.get(sensor, [])]
    days, day = [], start
    while day <= end:
        if not any(a <= day <= b for a, b in excluded):
            days.append(day)
        day += timedelta(days=1)
    return days


def fit_sigma(mu, observed, rng):
    best = None
    for sigma in config.LIVE_SIGMA_GRID:
        draws = np.stack([predictive_draws(m, 1.0, sigma, rng, 1000) for m in mu])
        low, high = np.quantile(draws, TAILS, axis=1)
        coverage = float(np.mean((observed >= low) & (observed <= high)))
        if best is None or abs(coverage - config.CI_LEVEL) < abs(best[1] - config.CI_LEVEL) - 1e-9:
            best = (sigma, coverage)
    return best


def coverage(mu, observed, sigma, rng):
    draws = np.stack([predictive_draws(m, 1.0, sigma, rng, 1000) for m in mu])
    low, high = np.quantile(draws, TAILS, axis=1)
    return float(np.mean((observed >= low) & (observed <= high)))


def calibrate(bundle, live_dir):
    with connect() as con:
        con.execute("CREATE TEMP TABLE cells AS SELECT * FROM read_parquet(?)", [str(config.INTERIM_DIR / "cells.parquet")])
        end = config.SNPP_END
        days = joint_days(end - timedelta(days=3 * config.LIVE_CALIBRATION_DAYS), end)[-config.LIVE_CALIBRATION_DAYS:]
        con.register("window_days", pd.DataFrame({"date": days}))
        observed = con.execute("""
            SELECT region, date, count(*) AS n FROM cells
            WHERE sensor = 'aqua' AND date IN (SELECT date FROM window_days) GROUP BY ALL
        """).df()
        frames = {source: con.execute("""
            SELECT cell_y, cell_x, date, month, region, n_points, frp_sum, frp_max, bright_max,
                scan_mean, track_mean, has_day, has_night
            FROM cells WHERE sensor = ? AND date IN (SELECT date FROM window_days)
            ORDER BY date, cell_y, cell_x
        """, [source]).df() for source in ("snpp", "noaa20")}
    observed["date"] = pd.to_datetime(observed.date).dt.date
    grid = pd.MultiIndex.from_product([days, config.REGIONS], names=["date", "region"])
    actual = observed.set_index(["date", "region"]).n.reindex(grid, fill_value=0)
    half = len(days) // 2
    result = {"window": [days[0].isoformat(), days[-1].isoformat()], "n_days": len(days), "sources": {}}
    for source, frame in frames.items():
        frame["date"] = pd.to_datetime(frame.date).dt.date
        scored = emulate(bundle, frame)
        scored["mu"] = scored.p + scored.r
        mu = scored.groupby(["date", "region"]).mu.sum().reindex(grid, fill_value=0.0)
        rng = np.random.default_rng(config.SEED)
        rows, national_mu = [], np.zeros(len(days))
        for region in config.REGIONS:
            m = mu.xs(region, level="region").to_numpy()
            o = actual.xs(region, level="region").to_numpy()
            drift = float(o.sum() / m.sum()) if m.sum() else 1.0
            sigma, fitted = fit_sigma(m * drift, o, rng)
            early = float(o[:half].sum() / m[:half].sum()) if m[:half].sum() else 1.0
            early_sigma, _ = fit_sigma(m[:half] * early, o[:half], rng)
            holdout = coverage(m[half:] * early, o[half:], early_sigma, rng)
            national_mu += m * drift
            rows.append({"region": region, "drift_factor": round(drift, 4), "sigma": sigma,
                         "coverage_in_sample": round(fitted, 4), "coverage_second_half": round(holdout, 4),
                         "mean_daily_observed": round(float(o.mean()), 2), "mean_daily_emulated": round(float(m.mean()), 2)})
        o = actual.groupby(level="date").sum().to_numpy()
        sigma, fitted = fit_sigma(national_mu, o, rng)
        rows.insert(0, {"region": config.NATIONAL, "drift_factor": 1.0,
                        "sigma": sigma, "coverage_in_sample": round(fitted, 4), "coverage_second_half": None,
                        "mean_daily_observed": round(float(o.mean()), 2),
                        "mean_daily_emulated": round(float(mu.groupby(level="date").sum().mean()), 2)})
        result["sources"][source] = {"regions": rows}
    result["method"] = ("Daily Aqua cell-days on jointly available days of the window. drift_factor = observed / emulated sum per region "
                        "(national: 1, because its point prediction is the sum of the adjusted regional ones). sigma = log-scale spread of a "
                        "Poisson-lognormal predictive distribution chosen from LIVE_SIGMA_GRID so that the 90% range covers the window. "
                        "coverage_second_half refits both on the first half and checks the second half.")
    write_json(live_dir / CALIBRATION_NAME, result)
    return result


def export(live_dir):
    live_dir.mkdir(parents=True, exist_ok=True)
    source = joblib.load(config.INTERIM_DIR / "emulator.joblib")
    bundle = {"model": source["model"], "features": source["features"], "region_categories": source["region_categories"],
              "rates": [{"region": row["region"], "month": int(row["month"]), "r": float(row["r"])} for row in source["rates"]],
              "train_years": source["train_years"]}
    assert bundle["features"] == FEATURES
    joblib.dump(bundle, live_dir / MODEL_NAME, compress=3)
    size = (live_dir / MODEL_NAME).stat().st_size
    if size >= 2 * 1024 * 1024:
        raise SystemExit(f"{MODEL_NAME} is {size} bytes; it must stay under 2 MB.")
    with connect() as con:
        mask = con.execute("SELECT instrument, cell_y, cell_x FROM read_parquet(?) ORDER BY ALL",
                           [str(config.INTERIM_DIR / "static_mask.parquet")]).fetchall()
        cells = con.execute("SELECT DISTINCT cell_y, cell_x, region FROM read_parquet(?) ORDER BY ALL",
                            [str(config.INTERIM_DIR / "cells.parquet")]).fetchall()
    write_json(live_dir / MASK_NAME, {
        "rule": "Static-source cells from scripts/cells.py (see data/interim/static_mask_validation.json); applied to NRT detections, which lack the type field.",
        "cells": [{"instrument": i, "cell_y": int(y), "cell_x": int(x)} for i, y, x in mask]})
    (live_dir / CELL_REGIONS_NAME).write_text(canonical({
        "rule": "Macroregion of every 0.1 degree cell seen in cells.parquet; other cells are assigned with scripts/regions.py.",
        "cells": [[int(y), int(x), region] for y, x, region in cells]}) + "\n")
    calibrate(bundle, live_dir)
    board = live_dir / SCOREBOARD_NAME
    if not board.is_file():
        write_json(board, empty_scoreboard())
    print(f"Exported {MODEL_NAME} ({size} bytes), {len(mask)} mask cells, {len(cells)} cell regions and the calibration.")


def parse_date(value):
    return date.fromisoformat(value)


def main():
    parser = argparse.ArgumentParser(description="Sealed daily Aqua predictions from VIIRS and their verification.")
    parser.add_argument("--live-dir", type=Path, default=config.LIVE_DIR)
    commands = parser.add_subparsers(dest="command", required=True)
    predict_parser = commands.add_parser("predict")
    predict_parser.add_argument("--date", type=parse_date, required=True)
    predict_parser.add_argument("--csv")
    predict_parser.add_argument("--source", choices=("auto", "snpp", "noaa20"), default="auto")
    predict_parser.add_argument("--force", action="store_true")
    score_parser = commands.add_parser("score")
    score_parser.add_argument("--date", type=parse_date, required=True)
    score_parser.add_argument("--csv")
    commands.add_parser("export")
    args = parser.parse_args()
    if args.command == "export":
        export(args.live_dir)
    elif args.command == "predict":
        result = predict(args.date, args.live_dir, args.csv, args.source, args.force)
        national = result["regions"][0]
        print(f"Prediction {result['date']} ({result['viirs_source']}): Aqua {national['aqua_predicted']} "
              f"[{national['aqua_low']}, {national['aqua_high']}] cell-days; sha256 {result['sha256']}")
    else:
        board = score(args.date, args.live_dir, args.csv)
        for row in board["rows"]:
            if row["date"] == args.date.isoformat() and row["region"] == config.NATIONAL:
                print(f"Score {row['date']}: observed {row['observed']} vs predicted {row['predicted']} "
                      f"[{row['low']}, {row['high']}], inside: {row['inside']}")


if __name__ == "__main__":
    main()
