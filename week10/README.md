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
