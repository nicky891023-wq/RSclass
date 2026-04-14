# ARIA v4.0 - Week 7 Disaster Accessibility Analysis

This repository now includes a completed Week 7 workflow for road-network disaster accessibility analysis in Hualien. The solution extends the earlier shelter, terrain, rainfall, and kriging work into a network-based accessibility model.

## Main Deliverables

- `ARIA_v4.ipynb`: Week 7 notebook that runs the integrated workflow
- `week7_aria_v4.py`: reusable analysis module used by the notebook
- `Week7_Output/data/hualien_network.graphml`: cached OSMnx road network after first successful run
- `Week7_Output/tables/accessibility_impact_table.csv`: before/after accessibility table
- `Week7_Output/tables/top5_bottlenecks.csv`: Top 5 bottleneck nodes with terrain proxy
- `Week7_Output/figures/top5_bottlenecks.png`: bottleneck map
- `Week7_Output/figures/isochrone_before_after.png`: isochrone comparison
- `Week7_Output/ai_strategy_prompt.txt`: AI strategy briefing prompt

## Week 7 Workflow

1. Load Hualien shelter data from `避難收容處所點位檔案v9 (1).csv`
2. Rebuild a Week 4 style terrain-risk proxy from shelter coordinates
3. Load or fetch the Hualien road network with OSMnx and archive it as GraphML
4. Compute edge travel time from road length and inferred speed
5. Calculate betweenness centrality and extract Top 5 bottleneck nodes
6. Sample Week 6 kriging rainfall from `Week6_Lab/kriging_rainfall.tif` at road-segment midpoints
7. Convert rainfall to congestion and remove near-impassable links
8. Compare 5-minute and 10-minute isochrone areas for five key shelters
9. Export tables, figures, and an AI command-center briefing prompt

## Running the Notebook

```bash
python create_week7_notebook.py
jupyter notebook ARIA_v4.ipynb
```

If the cached GraphML file does not exist, the first run will try to download road data from OpenStreetMap through OSMnx. Later runs load the cached `hualien_network.graphml` directly.

## Configuration

Week 7 parameters are stored in `.env`. The key values are:

- `WEEK7_PLACE_NAME`
- `WEEK7_GRAPHML_PATH`
- `WEEK7_RASTER_PATH`
- `WEEK7_RAINFALL_JSON`
- `ROAD_BREAK_CF`
- `WEEK7_FACILITY_COUNT`

## AI Diagnostic Log

### Missing road speed attributes

Problem: OSM road segments often do not include a usable `maxspeed` value.

Solution: `week7_aria_v4.py` parses numeric values when present, converts mph to km/h when needed, and falls back to a road-type default dictionary.

### Kriging raster sampling may return nodata

Problem: Edge midpoints can land on raster nodata cells.

Solution: The workflow samples the kriging raster at each edge midpoint and fills missing values with the median sampled rainfall to keep the network fully weighted.

### Network isolation after road breaks

Problem: Once high-congestion links are treated as broken roads, some facilities may lose access to the largest connected component.

Solution: The workflow builds a disaster graph with removed edges, then flags a facility as isolated when it falls outside the largest connected component or its 10-minute post-disaster isochrone collapses to a near-zero area.

### OSMnx network download repeat cost

Problem: Re-downloading the same road network is slow and brittle.

Solution: The workflow archives the projected network to `Week7_Output/data/hualien_network.graphml` and reuses it in later runs.

## Week 8 - ARIA v5.0 Matai'an Three-Act Auditor

- Pre item: `S2A_MSIL2A_20250615T023141_R046_T51QUG_20250615T070417`
- Mid item: `S2C_MSIL2A_20250911T022551_R046_T51QUG_20250911T055914`
- Post item: `S2B_MSIL2A_20251016T022559_R046_T51QUG_20251016T042804`
- Barrier lake area: 0.517 km²
- Landslide source area: 3.423 km²

## RSmeasure Archive

Older weekly source folders from `C:\Users\Wade\Desktop\ClassPhD\RSmeasure` are now archived under `RSmeasure_Archive/`, including `0303`, `0311`, `0322`, `0331`, `0407_upload`, `AQI_analysis`, and `ref`. This keeps the newer integrated workflow at the repo root while still preserving the original week-by-week materials in one GitHub repository.
- Debris flow area: 8.537 km²

### Coverage Gap Discussion

The Week 3 shelter layer and Week 7 bottlenecks both remain concentrated in the Hualien City corridor north of Matai'an. In this Week 8 audit, those legacy assets record zero direct debris-flow hits, while the Guangfu overlay captures the downstream assets exposed by the Sep 23, 2025 breach. The key lesson is that ARIA's pre-event footprint was operationally useful for Hualien City, but it did not extend far enough south to cover Guangfu's critical nodes.

### AI Diagnostic Log

- Mid-event STAC window: I compared the top three low-cloud candidates and selected the Sep 11, 2025 scene because it lines up with the reported peak lake size while keeping the Matai'an valley readable.
- Barrier-lake false positives: River-shadow noise dropped substantially after combining the turbid-water threshold with a west-of-121.33°E spatial gate.
- Landslide false positives: River sandbars triggered SWIR brightness, so I kept the `pre_B08 > 0.25` vegetation gate and tuned thresholds against a small truth set rather than relying on a single baseline pair.
