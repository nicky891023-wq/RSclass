## AI Strategic Briefing

### Exact Prompt

```text
You are an emergency management advisor for Hualien County during Typhoon Fung-wong.
Based on these ARIA v7.0 sensor fusion results, generate a strategic briefing that covers immediate evacuation priorities, resource allocation between high-confidence and SAR-only zones, current limitations, and additional data that would improve confidence.

- High confidence flood area: 0.000 km2
- SAR-only (cloudy) flood area: 0.934 km2
- False positives removed by topographic filter: 0.613 km2
- Cloud cover percentage: 100.0%
- SAR threshold: -18 dB, chosen as the ARIA default for conservative flood extraction
- NDWI threshold: 0, chosen for turbid storm water rather than clear water
```

### LLM Response

Immediate operations should prioritize the high-confidence flood zones because both SAR and optical evidence indicate water. These locations are the first candidates for evacuation checks, road closure verification, and rescue staging.

SAR-only cloudy zones should be treated as active watch and rapid reconnaissance areas. Radar can see through cloud, so these detections are operationally valuable, but teams should confirm them with field reports, UAV imagery, river gauges, or later cloud-free optical imagery before committing scarce heavy resources.

The main limitations are SAR speckle, possible radar shadow in steep terrain, the coarse timing mismatch between sensors, and uncertainty in NDWI over turbid water. Additional confidence would come from near-real-time water level gauges, road closure reports, UAV photos, updated DEM/LiDAR, and a second SAR pass from the same orbit.

### Reflection

The briefing correctly separates dual-sensor high-confidence areas from SAR-only cloudy zones, which is exactly the operational value of ARIA v7.0. It also identifies the biggest weakness: SAR detections in steep terrain can be radar shadow rather than water. What it cannot do from summary metrics alone is name exact villages or road segments, so the next step should overlay the confidence map with settlements, roads, and live disaster reports. I would therefore use the LLM response as a triage memo, not as a final evacuation order.

## ARIA v7.0 vs. v6.0 Comparison

| Metric                           | W9 Optical Only              | W10 Fused                     | Improvement               |
|:---------------------------------|:-----------------------------|:------------------------------|:--------------------------|
| Total detected flood/change area | 33.346 km2                   | 0.934 km2                     | -32.412 km2               |
| Cloud-covered area analyzed      | 0 km2                        | 0.934 km2 SAR-only class      | cloud gaps audited by SAR |
| False positives handled          | phantom water removed by SCL | 0.613 km2 flagged by slope    | adds terrain audit        |
| Confidence levels                | 3-zone                       | 4-class + false-positive flag | finer triage              |

Sentinel-1 SAR detected 0.934 km2 of flood-like water overall. Of this, 0.000 km2 is high-confidence dual-sensor evidence and 0.934 km2 is SAR-only detection inside cloud-masked pixels under 100.0% cloud cover. The topographic audit flagged 0.613 km2 as steep-slope false positives.