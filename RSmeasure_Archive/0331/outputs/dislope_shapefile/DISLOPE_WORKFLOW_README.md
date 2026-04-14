# Dislope Workflow

## Purpose

This workflow rebuilds the `順向坡目錄` dataset in `EPSG:3826`, recalculates `AREA` in `m^2`, and enriches the result with more complete attributes from:

`outputs/dislope_shapefile/05_環境地質基本圖`

Final output:

`outputs/dislope_shapefile/dislope_inventory.shp`

## Files

- `download_dislope_to_shapefile.py`
  Downloads `順向坡目錄` from the Landslide Cloud API, merges all supported counties, converts to `EPSG:3826`, and recalculates `AREA`.
- `enrich_dislope_from_envgeo.py`
  Matches the downloaded result against the local `05_環境地質基本圖` dislope layers and fills in richer attributes.
- `run_dislope_workflow.py`
  Runs the full workflow in sequence.

## Requirements

- Python environment with:
  - `geopandas`
  - `requests`
  - `pyogrio` or Fiona-compatible stack
  - `shapely`
- Internet access for the Landslide Cloud API
- Local source folder present:
  - `outputs/dislope_shapefile/05_環境地質基本圖`

## Full Rebuild

Run from the repo root:

```bash
python run_dislope_workflow.py
```

This does:

1. Download official `順向坡目錄` data from the API.
2. Merge counties and normalize fields.
3. Convert geometry to `EPSG:3826`.
4. Recalculate `AREA` from geometry in square meters.
5. Promote the rebuilt dataset to the formal output name.
6. Enrich attributes from `05_環境地質基本圖`.
7. Write the final `shapefile` and `geojson`.

## Step-by-Step Run

If you want to run each stage manually:

```bash
python download_dislope_to_shapefile.py
python enrich_dislope_from_envgeo.py
```

Note:

- `download_dislope_to_shapefile.py` first writes an intermediate 3826 dataset named:
  - `outputs/dislope_shapefile/dislope_inventory_3826_area_m2.shp`
- `enrich_dislope_from_envgeo.py` expects the formal input:
  - `outputs/dislope_shapefile/dislope_inventory.shp`
- `run_dislope_workflow.py` handles that rename/copy step automatically.

## Matching Logic

Attribute enrichment is done county by county.

Priority order:

1. `within`
   Match by representative point falling inside a source polygon.
2. `intersect`
   If not matched above, choose the intersecting source polygon with the largest overlap area.
3. `near100m`
   If still unmatched, assign the nearest source polygon within 100 meters.

Result fields added for QA:

- `MATCH_MTH`
- `MATCH_DST`

## Outputs

Primary outputs:

- `outputs/dislope_shapefile/dislope_inventory.shp`
- `outputs/dislope_shapefile/dislope_inventory.geojson`
- `outputs/dislope_shapefile/enrich_metadata.json`

Intermediate outputs:

- `outputs/dislope_shapefile/dislope_inventory_3826_area_m2.shp`
- `outputs/dislope_shapefile/download_metadata_3826_area_m2.json`

Backups:

- `outputs/dislope_shapefile/archive/dislope_inventory_pre_enrich.*`
- `outputs/dislope_shapefile/archive/dislope_inventory_wgs84.*`

## Important Notes

- The official API and the local `05_環境地質基本圖` are not perfectly identical, so a small number of features may remain unmatched after enrichment.
- The final shapefile keeps the rebuilt geometry and `AREA`, then fills additional source attributes where a match is found.
- If `dislope_inventory.shp` is open in GIS software, writing may fail. Close the layer first.

## Current Final Dataset

At the time this workflow was last run:

- CRS: `EPSG:3826`
- `AREA`: recalculated from geometry, unit `m^2`
- Total features: `19007`

