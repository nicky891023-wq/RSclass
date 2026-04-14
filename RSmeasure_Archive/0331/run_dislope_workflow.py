from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "outputs" / "dislope_shapefile"
DOWNLOAD_BASE = OUTPUT_DIR / "dislope_inventory_3826_area_m2"
FORMAL_BASE = OUTPUT_DIR / "dislope_inventory"
DOWNLOAD_METADATA = OUTPUT_DIR / "download_metadata_3826_area_m2.json"
FORMAL_METADATA = OUTPUT_DIR / "download_metadata.json"

SIDECAR_SUFFIXES = [".shp", ".shx", ".dbf", ".prj", ".cpg", ".geojson"]


def run_python(script_name: str) -> None:
    script_path = ROOT / script_name
    print(f"[run] {script_name}")
    subprocess.run([sys.executable, str(script_path)], check=True, cwd=ROOT)


def promote_download_outputs() -> None:
    print("[step] Promote downloaded 3826 files to formal output names")
    for suffix in SIDECAR_SUFFIXES:
        src = DOWNLOAD_BASE.with_suffix(suffix)
        dst = FORMAL_BASE.with_suffix(suffix)
        if not src.exists():
            raise FileNotFoundError(f"Missing expected output: {src}")
        if dst.exists():
            dst.unlink()
        shutil.copy2(src, dst)

    if DOWNLOAD_METADATA.exists():
        if FORMAL_METADATA.exists():
            FORMAL_METADATA.unlink()
        shutil.copy2(DOWNLOAD_METADATA, FORMAL_METADATA)


def main() -> None:
    run_python("download_dislope_to_shapefile.py")
    promote_download_outputs()
    run_python("enrich_dislope_from_envgeo.py")
    print("[done] Final output:")
    print(FORMAL_BASE.with_suffix(".shp"))


if __name__ == "__main__":
    main()
