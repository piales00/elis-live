from datetime import date
from math import inf
from pathlib import Path


COUNTRY = "Peru"
RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"
INTERIM_DIR = RAW_DIR.parent / "interim"
PROCESSED_DIR = RAW_DIR.parent / "processed"
GRID_DEG = 0.1
FIRE_TYPE = 0
MODIS_MIN_CONFIDENCE = 30
VIIRS_CONFIDENCE = ("n", "h")
CALIBRATION_YEARS = (2013, 2020)
TEST_YEARS = (2021, 2024)
HISTORY_YEARS = (2003, 2025)
FIRST_YEAR, LAST_YEAR = 2000, 2026
AQUA_START = date(2002, 7, 4)
VIIRS_START = date(2012, 1, 20)
REGIONS = ("amazonia", "sierra", "costa")
NATIONAL = "peru"
MIN_RECAPTURES = 5
CI_LEVEL = 0.90
BOOTSTRAP_N = 500
SEED = 42
ANOMALY_PERCENTILES = (25, 75, 90)
FRP_CLASSES = (0, 5, 20, inf)
EMULATOR_PARAMS = {
    "max_iter": 300,
    "learning_rate": 0.05,
    "max_leaf_nodes": 31,
    "early_stopping": True,
    "validation_fraction": 0.10,
    "random_state": SEED,
}
OUTAGES = {
    "aqua": [(date(2022, 4, 1), date(2022, 4, 16))],
    "snpp": [
        (date(2022, 7, 27), date(2022, 8, 10)),
        (date(2024, 5, 30), date(2024, 6, 3)),
        (date(2024, 7, 10), date(2024, 7, 15)),
        (date(2026, 3, 10), date(2026, 3, 12)),
        (date(2026, 4, 28), date(2026, 4, 30)),
        (date(2026, 6, 1), date(2026, 6, 2)),
        (date(2026, 7, 11), date(2026, 7, 16)),
        (date(2026, 8, 3), date(2026, 8, 3)),
    ],
    "terra": [],
}
DEGRADED = {"aqua": [(date(2020, 8, 16), date(2020, 9, 2))]}
TEST_SPLIT_DRIFT = ((2021, 2022), (2023, 2024))
TEST_MAX_REL_BIAS = 0.05
TEST_MIN_COVERAGE = 0.85
TEST_REPLICATES = 1000
EMULATOR_PERMUTATION_SAMPLE = 20000
EMULATOR_PERMUTATION_REPEATS = 5
RELIABILITY_BINS = 10
N_JOBS = 4
EMULATOR_LOGIT_PARAMS = {"C": 1.0, "solver": "lbfgs", "max_iter": 2000, "tol": 1e-4}
EMULATOR_CALIBRATION = {"method": "isotonic", "cv": 3, "max_ece": 0.02}
EMULATOR_CALIBRATION_YEARS = (2019, 2020)
SIMULTANEOUS_MAX_MINUTES = 20
DRIFT_START_YEAR = 2023
TERRA_BRIDGE_YEARS = (2003, 2011)
TERRA_BACKCAST_TEST_YEARS = (2003, 2006)
TERRA_BACKCAST_TRAIN_YEARS = (2007, 2011)
STRUCTURAL_ERROR_SOURCE = {"aqua": "aqua_vs_viirs_calibration", "terra": "terra_backcast"}
AQUA_BIAS_YEARS = CALIBRATION_YEARS
AQUA_BIAS_HIGH_SEASON = (7, 8, 9, 10, 11)
AQUA_BIAS_CORRECTION = True
LOW_CONFIDENCE_UNTIL = date(2002, 12, 31)
RAW_2026_DIR = RAW_DIR / "2026"
STATIC_MIN_SHARE = 0.5
STATIC_MIN_DETECTIONS = 5
STATIC_MASK_YEARS = (2012, 2025)
STATIC_VALIDATION_YEARS = (2024, 2025)
N20_RATIO_MAX_CV = 0.25
SNPP_END = date(2026, 11, 1)
LAST_DATA_DATE = date(2026, 11, 13)
PROJECT_ROOT = RAW_DIR.parents[1]
REGION_ID = "peru"
REGION_NAME = "Peru"
MACROREGION_NAMES = {"amazonia": "Amazon", "sierra": "Andes", "costa": "Coast"}
MACROREGION_DEPARTMENTS = {
    "amazonia": {"AMAZONAS", "LORETO", "MADRE DE DIOS", "SAN MARTIN", "UCAYALI"},
    "sierra": {
        "ANCASH",
        "APURIMAC",
        "AREQUIPA",
        "AYACUCHO",
        "CAJAMARCA",
        "CUSCO",
        "HUANCAVELICA",
        "HUANUCO",
        "JUNIN",
        "PASCO",
        "PUNO",
    },
    "costa": {"CALLAO", "ICA", "LA LIBERTAD", "LAMBAYEQUE", "LIMA", "MOQUEGUA", "PIURA", "TACNA", "TUMBES"},
}
DEPARTMENT_DISPLAY_NAMES = {
    "ANCASH": "Áncash",
    "APURIMAC": "Apurímac",
    "HUANUCO": "Huánuco",
    "JUNIN": "Junín",
    "MADRE DE DIOS": "Madre de Dios",
    "SAN MARTIN": "San Martín",
}
BOUNDARY_SIMPLIFICATION_DEG = 0.005
BOUNDARY_COORD_DIGITS = 4
MIN_YEAR = 2000
MAX_YEAR = 2026
MODIS_CONFIDENCE_MIN = 30
VIIRS_CONFIDENCE_ACCEPTED = {"n", "h"}
VEGETATION_TYPE = "0"
MODIS_YEARS = range(2000, 2026)
SNPP_YEARS = range(2012, 2026)
BOUNDARY_SOURCE_URL = (
    "https://geo.serfor.gob.pe/geoservicios/rest/services/Visor/"
    "Limites_Politicos_Administrativos/MapServer/0/query"
    "?where=1%3D1&outFields=IDDPTO%2CNOMBDEP%2CNOMBDEPID%2CDOCREG%2CFECREG%2COBSERV"
    "&returnGeometry=true&outSR=4326&f=geojson"
)
BOUNDARY_SOURCE_NAME = "INEI, límites censales referenciales publicados en el servicio de SERFOR"
BOUNDARY_SOURCE_FILE = RAW_DIR / "departamentos_peru_fuente.geojson"
EXTERNAL_DIR = RAW_DIR.parent / "external"
POWER_DIR = EXTERNAL_DIR / "power"
POWER_URL = "https://power.larc.nasa.gov/api/temporal/monthly/point"
POWER_COMMUNITY = "AG"
POWER_PARAMETERS = ("PRECTOTCORR", "T2M")
POWER_YEARS = (2000, 2026)
POWER_GRID_DEG = 1.5
POWER_MIN_POINTS = 4
FORECAST_LEADS = (1, 2, 3)
FORECAST_FIRE_WINDOW = 3
FORECAST_CLIMATE_WINDOW = 3
FORECAST_CLIMATE_LAG = 1
FORECAST_LOG_OFFSET = 1.0
FORECAST_RIDGE_ALPHAS = (0.1, 0.3, 1.0, 3.0, 10.0, 30.0, 100.0)
FORECAST_SEASON_MONTHS = (8, 9, 10)
FORECAST_SEASON_ORIGIN = 7
FORECAST_OOS_YEAR = 2026
FORECAST_DEMO_TRAIN_YEARS = (2003, 2011)
FORECAST_DEMO_TEST_YEARS = (2013, 2025)

UNDER_CACHE_VERSION = 2
UNDER_FIT_MAXITER = 600
UNDER_SIM_BOUNDS = {
    "mu": (-3.0, 4.0), "sigma": (0.3, 2.5), "delta_a": (-2.0, 3.0),
    "tau_a": (0.1, 2.0), "tau_s": (0.1, 2.0),
    "a_a": (-15.0, 5.0), "b_a": (0.1, 5.0), "pmax_a": (0.2, 0.999),
    "a_s": (-15.0, 5.0), "b_s": (0.1, 5.0), "pmax_s": (0.2, 0.999),
    "t0": (10.0, 400.0), "kappa": (0.0, 1.2),
}

UNDER_SIM = {'TAU_S': 0.4,
 'START': {'mu': 1.0,
           'sigma': 1.0,
           'delta_a': 1.0,
           'tau_a': 0.6,
           'tau_s': 0.4,
           'a_a': -5.0,
           'b_a': 2.0,
           'pmax_a': 0.9,
           'a_s': -2.0,
           'b_s': 2.5,
           'pmax_s': 0.9,
           't0': 80.0,
           'kappa': 0.5},
 'LOG_FRP_REF': 1.6094379124341003,
 'NOAA20_LAG': 50.0,
 'NOAA20_JITTER': 0.7,
 'OBSCURATION_SHARED_MINUTES': 30.0,
 'FIT_SAMPLE': 40000,
 'SMOOTH_WIDTH': 0.05,
 'REPLICATE_ACTIVE': 12000,
 'REPLICATE_DAYS': 2920,
 'REPLICATE_YEARS': 8,
 'REPLICATES': 20,
 'SLOW_REPLICATES': 25,
 'CALIBRATION_STARTS': (0.0, 0.2),
 'SIGMA_GRID': (0.5, 0.7, 0.9, 1.1, 1.4, 1.8, 2.3),
 'LIFETIME_MULTIPLIERS': (0.6, 1.6),
 'MIXTURE': {'weight': 0.3, 'shift': -2.0, 'scale': 0.7},
 'OBSCURATION': 0.15,
 'ACCEPTABLE_LOSS_RATIO': 2.0,
 'PASS_BIAS': 0.1,
 'PASS_COVERAGE': 0.8,
 'SCALES': {'probability': 0.01, 'cdf': 0.01, 'corr': 0.02, 'diff': 0.03, 'ratio': 0.005},
 'DEFAULT_GAP': {'mean': 5.0, 'sd': 35.0, 'limit': 100.0, 'residual_sd': 2.0}}

UNDER_ESTIMATOR = {'STABILITY_YEARS': (2018, 2022),
 'NOAA20_LAG': 50.0,
 'LOG_BIN': 0.1,
 'LOG_BIN_THREE': 0.2,
 'GAP_BIN': 5.0,
 'GH_NODES': 32,
 'HESSIAN_STEP': 0.0001,
 'FRP_FLOOR': 0.1,
 'S_CLASS_EDGES': (5.0, 20.0),
 'A_CLASS_EDGES': (10.0, 30.0),
 'COINCIDENCE_GAP_EDGES': (0.0, 20.0, 40.0, 60.0, inf),
 'FRP_QUANTILES': (0.1, 0.25, 0.5, 0.75, 0.9),
 'DRY_MONTHS': (7, 8, 9, 10, 11),
 'BOOTSTRAP': 200,
 'LATENT_CLASS_STARTS': 4,
 'LATENT_CLASS_DRAWS': 30,
 'MAX_UNSEEN_SHARE': 0.99,
 'PAD': 2048,
 'A2_START': [1.0,
              0.0,
              1.0,
              -0.5108256237659907,
              -0.6931471805599453,
              -5.0,
              0.6931471805599453,
              2.0,
              -2.0,
              0.9162907318741551,
              2.0],
 'LOG_FRP_REF': 1.6094379124341003}
UNDER_TIME_LIMIT_SECONDS = 1190

UNDER_SEED_BLOCK = 50
UNDER_SLOW_SEED_OFFSET = 25
ENSO_DIR = EXTERNAL_DIR / "enso"
ONI_URL = "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt"
ICEN_URL = "http://met.igp.gob.pe/datos/ICEN.txt"
FORECAST_SEASON_LEADS = (1, 4, 7, 10)
FORECAST_ENSO_INDICES = ("oni", "icen")
FORECAST_ENSO_LAG = 1
FORECAST_DROUGHT_WINDOWS = (3, 6, 12)
FORECAST_DROUGHT_LAG = 1
FORECAST_VARIANT_GROUPS = {
    "fire_only": (),
    "fire_enso": ("enso",),
    "fire_drought": ("drought",),
    "fire_enso_drought": ("enso", "drought"),
}
FORECAST_DEFAULT_VARIANT = "fire_only"
FORECAST_MIN_RPSS = 0.05
FORECAST_MIN_MAE_SKILL = 0.0
FORECAST_DEPARTMENT_MIN_SEASON = 100

CONTINUITY_SHUTDOWN = date(2023, 1, 1)
CONTINUITY_PRE_DRIFT_YEARS = (2013, 2022)
CONTINUITY_DRIFT_YEARS = (2023, 2026)
CONTINUITY_MIN_AQUA = 20
MODIS_SCIENCE_END_YEAR = 2027
LIVE_DIR = PROCESSED_DIR / "live"
FIRMS_AREA_URL = "https://firms.modaps.eosdis.nasa.gov/api/area/csv/{key}/{source}/{bbox}/1/{date}"
FIRMS_TIMEOUT_SECONDS = 120
PERU_BBOX = (-81.4, -18.4, -68.6, 0.0)
PERU_POINT_BUFFER_DEG = 0.01
LIVE_SOURCES = {
    "snpp": {"firms": "VIIRS_SNPP_NRT", "instrument": "viirs", "satellites": ("N", "SNPP")},
    "noaa20": {"firms": "VIIRS_NOAA20_NRT", "instrument": "viirs", "satellites": ("N20", "1", "J1")},
    "aqua": {"firms": "MODIS_NRT", "instrument": "modis", "satellites": ("Aqua", "A")},
}
LIVE_CALIBRATION_DAYS = 120
LIVE_SIGMA_GRID = tuple(round(0.05 * step, 2) for step in range(41))
LIVE_DRAWS = 4000
