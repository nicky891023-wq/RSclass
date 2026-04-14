import json
from pathlib import Path

import nbformat as nbf
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
WEEK8 = ROOT / "week8"
SUMMARY = json.loads((WEEK8 / "week8_summary.json").read_text(encoding="utf-8"))
IMPACT = pd.read_csv(WEEK8 / "impact_table.csv", encoding="utf-8-sig")
TUNING = pd.read_csv(ROOT / "output" / "week8_tables" / "landslide_threshold_tuning.csv", encoding="utf-8-sig")


def md(text):
    return nbf.v4.new_markdown_cell(text)


def code(text):
    return nbf.v4.new_code_cell(text)


nb = nbf.v4.new_notebook()
nb["cells"] = [
    md(
        "# ARIA v5.0 - Matai'an Three-Act Auditor\n\n"
        "This notebook completes the Week 8 class exercise and homework for the 2025 Matai'an Creek barrier-lake event. "
        "It uses a reproducible pipeline built on the Microsoft Planetary Computer Data API, with cached AOI crops so the notebook remains rerunnable on this machine."
    ),
    code(
        "from pathlib import Path\n"
        "import sys\n"
        "import json\n"
        "import pandas as pd\n"
        "import geopandas as gpd\n"
        "import matplotlib.pyplot as plt\n"
        "from IPython.display import Image, display, Markdown\n\n"
        "ROOT = Path.cwd()\n"
        "sys.path.append(str(ROOT))\n\n"
        "from week8.aria_v5_pipeline import (\n"
        "    run_pipeline, fetch_cube, apply_cloud_mask,\n"
        "    PRE_ITEM_ID, MID_ITEM_ID, POST_ITEM_ID,\n"
        "    nir_drop, swir_post, bsi_change, ndvi_change,\n"
        ")\n\n"
        "summary = run_pipeline()\n"
        "summary"
    ),
    md(
        "## Lab 1 - Scene Selection and TCI Quick-QA\n\n"
        "I selected **June 15, 2025** for the Pre scene because it had the cleanest cloud statistics in the window and the Matai'an valley itself remained readable, giving a stable forest baseline before Typhoon Wipha.\n\n"
        "I selected **September 11, 2025** for the Mid scene because it coincides with the reported peak lake stage and offers the clearest view of the new turbid-water body in the upper valley.\n\n"
        "I selected **October 16, 2025** for the Post scene because cloud cover drops to near-zero while the drained basin and downstream sediment patterns remain fresh enough to audit."
    ),
    md(
        "### Candidate Tables\n\n"
        f"#### PRE\n\n{pd.DataFrame(SUMMARY['candidates']['pre']).to_markdown(index=False)}\n\n"
        f"#### MID\n\n{pd.DataFrame(SUMMARY['candidates']['mid']).to_markdown(index=False)}\n\n"
        f"#### POST\n\n{pd.DataFrame(SUMMARY['candidates']['post']).to_markdown(index=False)}"
    ),
    code(
        "candidate_tables = {phase: pd.DataFrame(rows) for phase, rows in summary['candidates'].items()}\n"
        "for phase, table in candidate_tables.items():\n"
        "    display(Markdown(f'### {phase.upper()} Top-3 Candidates'))\n"
        "    display(table)\n"
        "    display(Image(filename=str(ROOT / 'output' / 'week8_figures' / f'{phase}_candidate_panel.png')))"
    ),
    md(
        "### Candidate Panels\n\n"
        "![PRE candidates](../output/week8_figures/pre_candidate_panel.png)\n\n"
        "![MID candidates](../output/week8_figures/mid_candidate_panel.png)\n\n"
        "![POST candidates](../output/week8_figures/post_candidate_panel.png)"
    ),
    md(
        "### Discussion - What the three acts show\n\n"
        "- **Act 1 / Pre**: the valley is still forested, with no standing lake visible near the later breach source.\n"
        "- **Act 2 / Mid**: the Sep 11 scene clearly shows a new turbid-water patch near the verified lake center around `(121.292, 23.696)`.\n"
        "- **Act 3 / Post**: the lake has drained, while fresh sediment signatures spread across the Guangfu side of the AOI."
    ),
    md("![Three-act TCI panel](../output/week8_figures/three_act_tci_panel.png)"),
    md(
        "## Lab 1 (cont.) - Four Change Metrics\n\n"
        "The notebook keeps the required reusable functions in code. I compute them for both **Pre → Mid** and **Pre → Post** so the same logic can support lake birth, source-scar detection, and downstream debris mapping."
    ),
    code(
        "cube_pre = apply_cloud_mask(fetch_cube(PRE_ITEM_ID))\n"
        "cube_mid = apply_cloud_mask(fetch_cube(MID_ITEM_ID))\n"
        "cube_post = apply_cloud_mask(fetch_cube(POST_ITEM_ID))\n\n"
        "metrics = {\n"
        "    'nir_drop_pre_mid': nir_drop(cube_pre, cube_mid),\n"
        "    'swir_post_mid': swir_post(cube_mid),\n"
        "    'bsi_change_pre_mid': bsi_change(cube_pre, cube_mid),\n"
        "    'ndvi_change_pre_mid': ndvi_change(cube_pre, cube_mid),\n"
        "    'nir_drop_pre_post': nir_drop(cube_pre, cube_post),\n"
        "    'swir_post_post': swir_post(cube_post),\n"
        "    'bsi_change_pre_post': bsi_change(cube_pre, cube_post),\n"
        "    'ndvi_change_pre_post': ndvi_change(cube_pre, cube_post),\n"
        "}\n"
        "{k: v.shape for k, v in metrics.items()}"
    ),
    code(
        "for name in [\n"
        "    'nir_drop_pre_mid.png', 'swir_post_mid.png', 'bsi_change_pre_mid.png', 'ndvi_change_pre_mid.png',\n"
        "    'nir_drop_pre_post.png', 'swir_post_post.png', 'bsi_change_pre_post.png', 'ndvi_change_pre_post.png'\n"
        "]:\n"
        "    display(Markdown(f'### {name.replace(\"_\", \" \").replace(\".png\", \"\")}'))\n"
        "    display(Image(filename=str(ROOT / 'output' / 'week8_figures' / name)))"
    ),
    md(
        "### Saved change-metric figures\n\n"
        "![nir drop pre mid](../output/week8_figures/nir_drop_pre_mid.png)\n\n"
        "![swir post mid](../output/week8_figures/swir_post_mid.png)\n\n"
        "![bsi change pre mid](../output/week8_figures/bsi_change_pre_mid.png)\n\n"
        "![ndvi change pre mid](../output/week8_figures/ndvi_change_pre_mid.png)\n\n"
        "![nir drop pre post](../output/week8_figures/nir_drop_pre_post.png)\n\n"
        "![swir post post](../output/week8_figures/swir_post_post.png)\n\n"
        "![bsi change pre post](../output/week8_figures/bsi_change_pre_post.png)\n\n"
        "![ndvi change pre post](../output/week8_figures/ndvi_change_pre_post.png)"
    ),
    md(
        "## Lab 2 - Detection Masks\n\n"
        "### C1. Barrier lake mask\n\n"
        "I tested `nir_mid` upper bounds of `0.12`, `0.15`, and `0.18` with the turbid-water rule plus a west-of-`121.33°E` spatial gate. "
        f"The best area match came from **`nir_mid < {SUMMARY['lake_threshold']}`**, producing a mapped lake area of **{SUMMARY['lake_area_km2']:.3f} km²**. "
        "This is smaller than the NCDR peak benchmark of `0.86 km²`, which suggests the mask remains intentionally conservative after cloud/shadow filtering."
    ),
    md("![Barrier lake mask](../output/week8_figures/barrier_lake_mask.png)"),
    md(
        "### C2. Landslide source scar mask\n\n"
        "I built a 10+10 truth set around the upper source area and tuned five threshold pairs using a confusion matrix. "
        f"The best pair was **nir_drop > {SUMMARY['landslide_best_thresholds']['nir_drop_min']}** and "
        f"**swir_post > {SUMMARY['landslide_best_thresholds']['swir_post_min']}**, with **F1 = {SUMMARY['landslide_best_thresholds']['f1']}**. "
        "I also added an upstream gate (`lon < 121.33`, `lat > 23.68`) so the source-scar layer stays physically tied to the headwall rather than spilling into Guangfu."
    ),
    code(
        "tuning = pd.read_csv(ROOT / 'output' / 'week8_tables' / 'landslide_threshold_tuning.csv', encoding='utf-8-sig')\n"
        "display(tuning)\n"
        "display(Image(filename=str(ROOT / 'output' / 'week8_figures' / 'landslide_source_mask.png')))"
    ),
    md(
        "#### Threshold tuning table\n\n"
        f"{TUNING.to_markdown(index=False)}\n\n"
        "![Landslide source mask](../output/week8_figures/landslide_source_mask.png)"
    ),
    md(
        "### C3. Debris flow footprint mask\n\n"
        "The debris rule is different from the landslide rule because the downstream surface is **wet mud over vegetation and paddies**, not bare rock at the source. "
        "That means the key signature is a **drop in NDVI** plus a **rise in BSI**, instead of the source-scar pattern of strong NIR loss plus bright SWIR on exposed material."
    ),
    md("![Debris flow mask](../output/week8_figures/debris_flow_mask.png)"),
    md(
        "## Multi-Layer Audit - Eyewitness Impact Table\n\n"
        "The impact table combines:\n\n"
        "- W3 shelters from the Hualien City range\n"
        "- W7 top-5 bottlenecks from the Hualien City corridor\n"
        "- A Week 8 Guangfu overlay with 5 required nodes plus 2 optional nodes\n\n"
        "Hit rules follow the assignment: inside for lake/debris, within 200 m for landslide."
    ),
    code(
        "impact = pd.read_csv(ROOT / 'week8' / 'impact_table.csv', encoding='utf-8-sig')\n"
        "impact.head(15)"
    ),
    md(
        "#### Impact table preview\n\n"
        f"{IMPACT.head(15).to_markdown(index=False)}"
    ),
    md(
        "### Coverage Gap Analysis\n\n"
        f"- **W3 shelters hit**: {SUMMARY['coverage_gap']['w3_hits']}\n"
        f"- **W7 bottlenecks hit**: {SUMMARY['coverage_gap']['w7_hits']}\n"
        f"- **Guangfu overlay nodes hit by debris**: {SUMMARY['coverage_gap']['guangfu_hits']}\n\n"
        "This is the main teaching point of Week 8: the legacy ARIA coverage was still concentrated north around Hualien City, so it missed the southward operational exposure in Guangfu. "
        "ARIA v5.0 fixes that by adding a dedicated local overlay and verifying the event with actual post-scene evidence instead of only upstream risk proxies."
    ),
    md("![Final impact map](../output/week8_figures/final_impact_map.png)"),
    md(
        "## Bonus - AI Advisor Operational Brief\n\n"
        "I generated the brief from the impact table and the three-act summary. The final text is reproduced below."
    ),
    md(
        "### Operational Brief\n\n"
        + SUMMARY["operational_brief"]
    ),
    md(
        "## Professional Standards Check\n\n"
        "- `.env` updated with Week 8 STAC settings and reproducible item IDs\n"
        "- `mataian_detections.gpkg` written with `barrier_lake`, `landslide_source`, and `debris_flow` layers\n"
        "- `impact_table.csv` exported\n"
        "- `output/` includes candidate panels, three-act panel, metric maps, masks, and final impact map\n"
        "- `README.md` includes chosen scene IDs, coverage gap discussion, and AI diagnostic log"
    ),
]

nb["metadata"]["kernelspec"] = {"display_name": "Python 3", "language": "python", "name": "python3"}
nb["metadata"]["language_info"] = {"name": "python", "version": "3.13"}

for name in ["ARIA_v5_mataian.ipynb", "Week8-Student.ipynb"]:
    (WEEK8 / name).write_text(nbf.writes(nb), encoding="utf-8")
