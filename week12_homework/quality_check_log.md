# Week12 Homework Quality Check Log

## Cycle 1 - strict baseline

- Note: Baseline with stricter ROI patches; inspect KMZ coverage and initial SWCB overlay.
- ROI target/radius/max patches: 450 / 3 / 10
- RF trees/min leaf: 160 / 2
- Test accuracy: 0.940
- OOB score: 0.934
- Macro F1 / Weighted F1: 0.923 / 0.940
- SWCB IoU / precision / recall: 0.054 / 0.103 / 0.102
- Validation: REVIEW

| Check | Status | Detail |
|---|---:|---|
| kmeans_classification.png | PASS | 791,025 bytes, image_std=73.69 |
| rf_classification.png | PASS | 770,547 bytes, image_std=79.11 |
| confusion_matrix.png | PASS | 40,937 bytes, image_std=59.22 |
| swcb_overlay.png | PASS | 1,640,573 bytes, image_std=82.38 |
| class_area_stats.csv | REVIEW | 407 bytes |
| area_stats_sum | PASS | sum=100.000 |
| training_kmz_exists | REVIEW | C:\Users\Wade\Desktop\ClassPhD\RSmeasure\0512\homework_week12\data\taroko_training_rois.kmz |
| swcb_kml_exists | PASS | C:\Users\Wade\Desktop\ClassPhD\RSmeasure\0512\homework_week12\data\20240802新生崩塌地.kml |
| roi_class_coverage | PASS | {"Water": 455, "Forest": 402, "Cropland": 361, "Bare/Landslide": 256, "Built-up": 251} |
| oob_test_gap | PASS | 0.006 |
| swcb_reference_nonempty | PASS | 1216 polygons |

## Cycle 2 - expanded ROI and balanced RF

- Note: Expanded sparse cropland/built-up ROI coverage and increased forest size.
- ROI target/radius/max patches: 750 / 4 / 14
- RF trees/min leaf: 220 / 1
- Test accuracy: 0.949
- OOB score: 0.942
- Macro F1 / Weighted F1: 0.934 / 0.949
- SWCB IoU / precision / recall: 0.013 / 0.069 / 0.015
- Validation: REVIEW

| Check | Status | Detail |
|---|---:|---|
| kmeans_classification.png | PASS | 791,025 bytes, image_std=73.69 |
| rf_classification.png | PASS | 810,062 bytes, image_std=81.00 |
| confusion_matrix.png | PASS | 44,625 bytes, image_std=63.33 |
| swcb_overlay.png | PASS | 1,642,051 bytes, image_std=82.92 |
| class_area_stats.csv | REVIEW | 397 bytes |
| area_stats_sum | PASS | sum=100.000 |
| training_kmz_exists | REVIEW | C:\Users\Wade\Desktop\ClassPhD\RSmeasure\0512\homework_week12\data\taroko_training_rois.kmz |
| swcb_kml_exists | PASS | C:\Users\Wade\Desktop\ClassPhD\RSmeasure\0512\homework_week12\data\20240802新生崩塌地.kml |
| roi_class_coverage | PASS | {"Water": 783, "Forest": 816, "Cropland": 785, "Bare/Landslide": 422, "Built-up": 555} |
| oob_test_gap | PASS | 0.006 |
| swcb_reference_nonempty | PASS | 1216 polygons |

## Cycle 3 - final corrected deliverables

- Note: Final rerun after confirming KMZ parse, official SWCB KML, output files, and area totals.
- ROI target/radius/max patches: 1050 / 5 / 16
- RF trees/min leaf: 300 / 1
- Test accuracy: 0.939
- OOB score: 0.945
- Macro F1 / Weighted F1: 0.930 / 0.939
- SWCB IoU / precision / recall: 0.009 / 0.028 / 0.012
- Validation: REVIEW

| Check | Status | Detail |
|---|---:|---|
| kmeans_classification.png | PASS | 791,025 bytes, image_std=73.69 |
| rf_classification.png | PASS | 820,406 bytes, image_std=79.59 |
| confusion_matrix.png | PASS | 43,860 bytes, image_std=64.33 |
| swcb_overlay.png | PASS | 1,641,134 bytes, image_std=82.76 |
| class_area_stats.csv | REVIEW | 413 bytes |
| area_stats_sum | PASS | sum=100.000 |
| training_kmz_exists | PASS | C:\Users\Wade\Desktop\ClassPhD\RSmeasure\0512\homework_week12\data\taroko_training_rois.kmz |
| swcb_kml_exists | PASS | C:\Users\Wade\Desktop\ClassPhD\RSmeasure\0512\homework_week12\data\20240802新生崩塌地.kml |
| roi_class_coverage | PASS | {"Water": 1116, "Forest": 1072, "Cropland": 1154, "Bare/Landslide": 598, "Built-up": 941} |
| oob_test_gap | PASS | -0.006 |
| swcb_reference_nonempty | PASS | 1216 polygons |

## Notebook final rerun

- Note: Executed notebook rerun after three script quality cycles.
- ROI target/radius/max patches: 1050 / 5 / 16
- RF trees/min leaf: 300 / 1
- Test accuracy: 0.939
- OOB score: 0.945
- Macro F1 / Weighted F1: 0.930 / 0.939
- SWCB IoU / precision / recall: 0.009 / 0.028 / 0.012
- Validation: PASS

| Check | Status | Detail |
|---|---:|---|
| kmeans_classification.png | PASS | 791,025 bytes, image_std=73.69 |
| rf_classification.png | PASS | 758,312 bytes, image_std=78.31 |
| confusion_matrix.png | PASS | 64,458 bytes, image_std=61.17 |
| swcb_overlay.png | PASS | 1,641,134 bytes, image_std=82.76 |
| class_area_stats.csv | PASS | 413 bytes |
| area_stats_sum | PASS | sum=100.000 |
| training_kmz_exists | PASS | C:\Users\Wade\Desktop\ClassPhD\RSmeasure\0512\homework_week12\data\taroko_training_rois.kmz |
| swcb_kml_exists | PASS | C:\Users\Wade\Desktop\ClassPhD\RSmeasure\0512\homework_week12\data\20240802新生崩塌地.kml |
| roi_class_coverage | PASS | {"Water": 1116, "Forest": 1072, "Cropland": 1154, "Bare/Landslide": 598, "Built-up": 941} |
| oob_test_gap | PASS | -0.006 |
| swcb_reference_nonempty | PASS | 1216 polygons |

## notebook_final_rerun

- Note: Notebook final rerun using cached Sentinel-2 and official SWCB KML.
- ROI target/radius/max patches: 1050 / 5 / 16
- RF trees/min leaf: 300 / 1
- Test accuracy: 0.939
- OOB score: 0.945
- Macro F1 / Weighted F1: 0.930 / 0.939
- SWCB IoU / precision / recall: 0.009 / 0.028 / 0.012
- Validation: PASS

| Check | Status | Detail |
|---|---:|---|
| kmeans_classification.png | PASS | 791,025 bytes, image_std=73.69 |
| rf_classification.png | PASS | 758,312 bytes, image_std=78.31 |
| confusion_matrix.png | PASS | 64,458 bytes, image_std=61.17 |
| swcb_overlay.png | PASS | 1,641,134 bytes, image_std=82.76 |
| class_area_stats.csv | PASS | 413 bytes |
| area_stats_sum | PASS | sum=100.000 |
| training_kmz_exists | PASS | C:\Users\Wade\Desktop\ClassPhD\RSmeasure\0512\homework_week12\data\taroko_training_rois.kmz |
| swcb_kml_exists | PASS | C:\Users\Wade\Desktop\ClassPhD\RSmeasure\0512\homework_week12\data\20240802新生崩塌地.kml |
| roi_class_coverage | PASS | {"Water": 1116, "Forest": 1072, "Cropland": 1154, "Bare/Landslide": 598, "Built-up": 941} |
| oob_test_gap | PASS | -0.006 |
| swcb_reference_nonempty | PASS | 1216 polygons |

## notebook_final_rerun

- Note: Notebook final rerun using cached Sentinel-2 and official SWCB KML.
- ROI target/radius/max patches: 1050 / 5 / 16
- RF trees/min leaf: 300 / 1
- Test accuracy: 0.939
- OOB score: 0.945
- Macro F1 / Weighted F1: 0.930 / 0.939
- SWCB IoU / precision / recall: 0.009 / 0.028 / 0.012
- Validation: PASS

| Check | Status | Detail |
|---|---:|---|
| kmeans_classification.png | PASS | 791,025 bytes, image_std=73.69 |
| rf_classification.png | PASS | 758,312 bytes, image_std=78.31 |
| confusion_matrix.png | PASS | 64,458 bytes, image_std=61.17 |
| swcb_overlay.png | PASS | 1,641,134 bytes, image_std=82.76 |
| class_area_stats.csv | PASS | 413 bytes |
| area_stats_sum | PASS | sum=100.000 |
| training_kmz_exists | PASS | C:\Users\Wade\Desktop\ClassPhD\RSmeasure\0512\homework_week12\data\taroko_training_rois.kmz |
| swcb_kml_exists | PASS | C:\Users\Wade\Desktop\ClassPhD\RSmeasure\0512\homework_week12\data\20240802新生崩塌地.kml |
| roi_class_coverage | PASS | {"Water": 1116, "Forest": 1072, "Cropland": 1154, "Bare/Landslide": 598, "Built-up": 941} |
| oob_test_gap | PASS | -0.006 |
| swcb_reference_nonempty | PASS | 1216 polygons |

## Notebook final rerun

- Note: Executed notebook rerun after three script quality cycles.
- ROI target/radius/max patches: 1050 / 5 / 16
- RF trees/min leaf: 300 / 1
- Test accuracy: 0.939
- OOB score: 0.945
- Macro F1 / Weighted F1: 0.930 / 0.939
- SWCB IoU / precision / recall: 0.009 / 0.028 / 0.012
- Validation: PASS

| Check | Status | Detail |
|---|---:|---|
| kmeans_classification.png | PASS | 791,025 bytes, image_std=73.69 |
| rf_classification.png | PASS | 758,312 bytes, image_std=78.31 |
| confusion_matrix.png | PASS | 64,458 bytes, image_std=61.17 |
| swcb_overlay.png | PASS | 1,641,134 bytes, image_std=82.76 |
| class_area_stats.csv | PASS | 413 bytes |
| area_stats_sum | PASS | sum=100.000 |
| training_kmz_exists | PASS | C:\Users\Wade\Desktop\ClassPhD\RSmeasure\0512\homework_week12\data\taroko_training_rois.kmz |
| swcb_kml_exists | PASS | C:\Users\Wade\Desktop\ClassPhD\RSmeasure\0512\homework_week12\data\20240802新生崩塌地.kml |
| roi_class_coverage | PASS | {"Water": 1116, "Forest": 1072, "Cropland": 1154, "Bare/Landslide": 598, "Built-up": 941} |
| oob_test_gap | PASS | -0.006 |
| swcb_reference_nonempty | PASS | 1216 polygons |

## notebook_final_rerun

- Note: Notebook final rerun using cached Sentinel-2 and official SWCB KML.
- ROI target/radius/max patches: 1050 / 5 / 16
- RF trees/min leaf: 300 / 1
- Test accuracy: 0.939
- OOB score: 0.945
- Macro F1 / Weighted F1: 0.930 / 0.939
- SWCB IoU / precision / recall: 0.009 / 0.028 / 0.012
- Validation: PASS

| Check | Status | Detail |
|---|---:|---|
| kmeans_classification.png | PASS | 791,025 bytes, image_std=73.69 |
| rf_classification.png | PASS | 758,312 bytes, image_std=78.31 |
| confusion_matrix.png | PASS | 64,458 bytes, image_std=61.17 |
| swcb_overlay.png | PASS | 1,641,134 bytes, image_std=82.76 |
| class_area_stats.csv | PASS | 413 bytes |
| area_stats_sum | PASS | sum=100.000 |
| training_kmz_exists | PASS | C:\Users\Wade\Desktop\ClassPhD\RSmeasure\0512\homework_week12\data\taroko_training_rois.kmz |
| swcb_kml_exists | PASS | C:\Users\Wade\Desktop\ClassPhD\RSmeasure\0512\homework_week12\data\20240802新生崩塌地.kml |
| roi_class_coverage | PASS | {"Water": 1116, "Forest": 1072, "Cropland": 1154, "Bare/Landslide": 598, "Built-up": 941} |
| oob_test_gap | PASS | -0.006 |
| swcb_reference_nonempty | PASS | 1216 polygons |

## Notebook final rerun

- Note: Executed notebook rerun after three script quality cycles.
- ROI target/radius/max patches: 1050 / 5 / 16
- RF trees/min leaf: 300 / 1
- Test accuracy: 0.939
- OOB score: 0.945
- Macro F1 / Weighted F1: 0.930 / 0.939
- SWCB IoU / precision / recall: 0.009 / 0.028 / 0.012
- Validation: PASS

| Check | Status | Detail |
|---|---:|---|
| kmeans_classification.png | PASS | 791,025 bytes, image_std=73.69 |
| rf_classification.png | PASS | 758,312 bytes, image_std=78.31 |
| confusion_matrix.png | PASS | 64,458 bytes, image_std=61.17 |
| swcb_overlay.png | PASS | 1,641,134 bytes, image_std=82.76 |
| class_area_stats.csv | PASS | 413 bytes |
| area_stats_sum | PASS | sum=100.000 |
| training_kmz_exists | PASS | C:\Users\Wade\Desktop\ClassPhD\RSmeasure\0512\homework_week12\data\taroko_training_rois.kmz |
| swcb_kml_exists | PASS | C:\Users\Wade\Desktop\ClassPhD\RSmeasure\0512\homework_week12\data\20240802新生崩塌地.kml |
| roi_class_coverage | PASS | {"Water": 1116, "Forest": 1072, "Cropland": 1154, "Bare/Landslide": 598, "Built-up": 941} |
| oob_test_gap | PASS | -0.006 |
| swcb_reference_nonempty | PASS | 1216 polygons |

