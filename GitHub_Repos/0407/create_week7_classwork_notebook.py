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
        "# Week 7 Class Practice - ARIA v4.0 Core Lab\n"
        "\n"
        "This notebook focuses on the in-class core tasks: road network loading, bottleneck analysis, dynamic weights, and accessibility shrinkage."
    ),
    code(
        "import pandas as pd\n"
        "from IPython.display import display\n"
        "\n"
        "from week7_aria_v4 import run_week7_analysis\n"
        "\n"
        "pd.set_option('display.max_columns', 20)\n"
    ),
    md("## Captain's Log 1: Run the shared Week 7 analysis pipeline"),
    code(
        "results = run_week7_analysis()\n"
        "bottlenecks = results['bottlenecks']\n"
        "accessibility = results['accessibility']\n"
        "print('Road network loaded and dynamic accessibility analysis complete.')\n"
    ),
    md("## Captain's Log 2: Top 5 bottleneck nodes"),
    code(
        "bottleneck_cols = ['node_id', 'centrality', 'terrain_risk']\n"
        "if 'nearest_hazard_m' in bottlenecks.columns:\n"
        "    bottleneck_cols += ['nearest_hazard_m', 'CODE']\n"
        "display(bottlenecks[bottleneck_cols])\n"
    ),
    md("## Captain's Log 3: Core accessibility impact table"),
    code(
        "display(\n"
        "    accessibility[\n"
        "        [\n"
        "            'facility_name',\n"
        "            'pre_5min_km2',\n"
        "            'post_5min_km2',\n"
        "            'shrinkage_5_pct',\n"
        "            'pre_10min_km2',\n"
        "            'post_10min_km2',\n"
        "            'shrinkage_10_pct',\n"
        "            'isolated',\n"
        "        ]\n"
        "    ]\n"
        ")\n"
    ),
]

nb["metadata"]["kernelspec"] = {
    "display_name": "Python 3",
    "language": "python",
    "name": "python3",
}
nb["metadata"]["language_info"] = {"name": "python", "version": "3.x"}

(ROOT / "Week7_Class_Practice.ipynb").write_text(nbf.writes(nb), encoding="utf-8")
