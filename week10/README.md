# Week 10 - ARIA v7.0 All-Weather Auditor

This folder contains the Week 10 classroom practice and homework submission for Remote Sensing & Spatial Information Analysis.

## Main Deliverables

- `Week10-Student-Completed.ipynb` - completed classroom practice notebook, with a final discussion summary
- `Week10_ARIA_v70_Wade.ipynb` - full homework report notebook with tables, figures, discussion, AI briefing, and verification
- `week10_outputs/task1_sar_detection_panel.png` - SAR raw/filter/mask/overlay panel
- `week10_outputs/task2_confidence_map.png` - four-class ARIA v7.0 fusion map
- `week10_outputs/task3_topographic_audit.png` - before/after slope audit figure
- `week10_outputs/task4_ai_briefing_and_report.md` - exact AI prompt, response, reflection, and W9/W10 comparison

## Reproducibility

- `generate_week10_submission.py` regenerates the Week 10 outputs from Planetary Computer STAC.
- `.env.example` records the parameters used for this run.
- The real `.env` is intentionally not committed.

## Final Metrics

| Metric | Value |
|---|---:|
| Cloud cover | 100.0% |
| SAR flood-like water area | 0.934 km2 |
| High-confidence dual-sensor area | 0.000 km2 |
| SAR-only cloudy flood candidate area | 0.934 km2 |
| Steep-slope false positives flagged | 0.613 km2 |
| Post-audit flood candidate area | 0.321 km2 |

## Interpretation

The selected Sentinel-2 optical scene is fully cloud-covered, so ARIA v7.0 correctly produces no high-confidence dual-sensor pixels. The key result is the SAR-only cloudy class: Sentinel-1 still detects 0.934 km2 of flood-like water candidates, then the DEM slope audit flags 0.613 km2 as likely terrain-related artifacts. This demonstrates the Week 10 lesson: SAR does not replace validation, but it keeps the disaster assessment alive when optical imagery is unusable.

## Course Key Points

- **SAR all-weather observation:** Sentinel-1 uses microwave radar, so it can provide evidence when Sentinel-2 optical imagery is blocked by typhoon clouds.
- **Backscatter physics:** Smooth water often appears dark in VV dB because specular reflection sends energy away from the sensor.
- **Speckle control:** Raw SAR should not be thresholded directly. The workflow applies a 5 x 5 median filter before extracting `VV < -18 dB` water candidates.
- **Sensor fusion:** High Confidence requires both SAR and non-cloudy NDWI evidence. Under 100% cloud cover, the honest class is SAR Only (Cloudy), not High Confidence.
- **Topographic audit:** SAR dark pixels on steep slopes may be radar shadow, layover, or foreshortening rather than water. DEM slope > 25 degrees is used as a false-positive warning.

## How to Read the Figures

| Figure | What it means | How it was produced |
|---|---|---|
| `task1_sar_detection_panel.png` | Shows raw SAR, filtered SAR, binary flood mask, and overlay. It demonstrates that the final water candidate map comes from filtered low-backscatter SAR pixels, not from raw noisy SAR. | Sentinel-1 RTC VV -> dB conversion -> 5 x 5 median filter -> `VV < -18 dB` -> morphology and connected-component cleanup. |
| `task2_confidence_map.png` | Shows ARIA v7.0 confidence classes. In this run, cloud cover is 100%, so there is no high-confidence optical-plus-SAR class; the operational class is SAR Only (Cloudy). | SAR water mask + Sentinel-2 NDWI mask + Sentinel-2 SCL cloud mask -> four-class fusion rule. |
| `task3_topographic_audit.png` | Shows the fusion result before audit, DEM-derived slope, and post-audit result. It explains why some dark SAR detections are physically suspicious on steep slopes. | Fusion map + Copernicus DEM slope -> flag flood detections where slope > 25 degrees. |

## Operation History

1. Checked for local `S1_Hualien_dB.tif`; it was not present.
2. Streamed Sentinel-1 RTC VV from Planetary Computer for the Hualien BBOX.
3. Converted SAR linear backscatter to dB and applied median filtering.
4. Extracted SAR flood-like water with `VV < -18 dB`.
5. Loaded Sentinel-2 L2A and created NDWI plus SCL cloud masks.
6. Fused SAR, NDWI, and cloud mask into four confidence classes.
7. Loaded Copernicus DEM, calculated slope, and flagged slope > 25 degrees as likely false-positive terrain artifacts.
8. Generated figures, tables, AI briefing, and the final notebook report.
