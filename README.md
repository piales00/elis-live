# Elis live feed

Daily sealed predictions for [Elis](https://github.com/piales00/Elis), a harmonized MODIS–VIIRS fire record for Peru (NASA Space Apps 2026).

Every day a GitHub Actions job:

1. **Predicts** how many fire cell-days MODIS Aqua will see in Peru (by region, with a 90% range), using only VIIRS near-real-time detections from NASA FIRMS and the Elis MODIS emulator. Each prediction is saved with the SHA-256 of its content, its input data, the model and the calibration, and is never overwritten.
2. **Scores** the prediction made the day before against what Aqua actually saw, and updates the scoreboard.

The commit history is the seal: each prediction is committed before the Aqua data it is compared with.

| File | Content |
|---|---|
| `data/processed/live/predictions/YYYY-MM-DD.json` | Sealed prediction for one day |
| `data/processed/live/scoreboard.json` | Predicted vs observed, inside the range or not, running summary |

The Elis web app reads `scoreboard.json` directly from this repository. This repository is only a data feed; the Elis project itself lives in [piales00/Elis](https://github.com/piales00/Elis).

Unit: fire cell-days (a ~11 km grid cell with at least one active-fire detection on a date). Data: NASA FIRMS (VIIRS NOAA-20/S-NPP and MODIS Aqua NRT).
