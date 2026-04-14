from pathlib import Path

import nbformat as nbf


ROOT = Path(__file__).resolve().parent


def md(text: str):
    return nbf.v4.new_markdown_cell(text)


def code(text: str):
    return nbf.v4.new_code_cell(text)


nb = nbf.v4.new_notebook()
nb["cells"] = [
    md(
        "# ARIA v4.0 - Week 7\n"
        "\n"
        "This notebook completes the Week 7 in-class lab and homework in sequence.\n"
        "\n"
        "## Workflow\n"
        "- Captain's Log 1: Load configuration and reusable Week 3-6 assets\n"
        "- Captain's Log 2: Build or load the Hualien road network and travel time attributes\n"
        "- Captain's Log 3: Diagnose bottlenecks and terrain vulnerability\n"
        "- Captain's Log 4: Apply rainfall-driven congestion and disaster road breaks\n"
        "- Captain's Log 5: Compare pre/post-disaster accessibility for five key shelters\n"
        "- Captain's Log 6: Export GraphML, tables, figures, and AI briefing prompt\n"
    ),
    code(
        "import pandas as pd\n"
        "from IPython.display import display\n"
        "\n"
        "from week7_aria_v4 import run_week7_analysis, OUTPUT_DIR, FIG_DIR, TABLE_DIR\n"
        "\n"
        "pd.set_option('display.max_columns', 20)\n"
    ),
    md(
        "## Captain's Log 1: Execute the integrated Week 7 pipeline\n"
        "\n"
        "This cell performs the full road-network, bottleneck, rainfall, and accessibility workflow."
    ),
    code(
        "results = run_week7_analysis()\n"
        "bottlenecks = results['bottlenecks']\n"
        "facilities = results['facilities']\n"
        "accessibility = results['accessibility']\n"
        "\n"
        "print(f\"Output folder: {OUTPUT_DIR}\")\n"
        "print(f\"Graph nodes: {results['graph'].number_of_nodes()}\")\n"
        "print(f\"Graph edges: {results['graph'].number_of_edges()}\")\n"
        "print(f\"Facilities analysed: {len(accessibility)}\")\n"
    ),
    md("## Captain's Log 2: Top 5 bottleneck nodes with Week 4 terrain-risk proxy"),
    code(
        "bottleneck_cols = ['node_id', 'centrality', 'terrain_risk', 'mean_elevation', 'max_slope']\n"
        "if 'nearest_hazard_m' in bottlenecks.columns:\n"
        "    bottleneck_cols += ['nearest_hazard_m', 'CODE']\n"
        "elif 'nearest_shelter_m' in bottlenecks.columns:\n"
        "    bottleneck_cols += ['nearest_shelter_m']\n"
        "display(bottlenecks[bottleneck_cols])\n"
    ),
    md("## Captain's Log 3: Selected key shelters for accessibility comparison"),
    code(
        "display(\n"
        "    facilities[\n"
        "        ['shelter_id', 'facility_name', 'capacity', 'terrain_risk', 'nearest_node']\n"
        "    ]\n"
        ")\n"
    ),
    md("## Captain's Log 4: Accessibility impact table"),
    code(
        "impact_view = accessibility[\n"
        "    [\n"
        "        'facility_name',\n"
        "        'terrain_risk',\n"
        "        'pre_5min_km2',\n"
        "        'post_5min_km2',\n"
        "        'shrinkage_5_pct',\n"
        "        'pre_10min_km2',\n"
        "        'post_10min_km2',\n"
        "        'shrinkage_10_pct',\n"
        "        'isolated',\n"
        "    ]\n"
        "]\n"
        "display(impact_view)\n"
    ),
    md("## Captain's Log 5: Rainfall-station summary from Week 5 data"),
    code("display(results['rainfall_stations'].sort_values('rain_1hr', ascending=False).head(10))"),
    md("## Captain's Log 6: AI strategy briefing prompt"),
    code("print(results['ai_prompt'])"),
    md("## Deliverables"),
    code(
        "print('Figures:')\n"
        "for path in sorted(FIG_DIR.glob('*')):\n"
        "    print('-', path)\n"
        "\n"
        "print('\\nTables:')\n"
        "for path in sorted(TABLE_DIR.glob('*')):\n"
        "    print('-', path)\n"
        "\n"
        "print('\\nOther outputs:')\n"
        "for path in sorted(OUTPUT_DIR.glob('*.txt')):\n"
        "    print('-', path)\n"
    ),
]

nb["metadata"]["kernelspec"] = {
    "display_name": "Python 3",
    "language": "python",
    "name": "python3",
}
nb["metadata"]["language_info"] = {"name": "python", "version": "3.x"}

(ROOT / "ARIA_v4.ipynb").write_text(nbf.writes(nb), encoding="utf-8")
