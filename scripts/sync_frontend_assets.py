"""Copy generated demo projects/reports into the installable offline PWA."""

from pathlib import Path
from shutil import copy2

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "frontend" / "public" / "demo"
REPORTS = PUBLIC / "reports"


def main() -> None:
    PUBLIC.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    for project_path in sorted((ROOT / "examples").glob("nf-demo-*.json")):
        stem = project_path.stem
        result_path = ROOT / "examples" / "generated" / f"{stem}.json"
        copy2(project_path, PUBLIC / f"{stem}.project.json")
        copy2(result_path, PUBLIC / f"{stem}.result.json")
        for extension in ("pdf", "docx", "xlsx", "csv", "json"):
            source = ROOT / "examples" / "generated" / f"{stem}.{extension}"
            copy2(source, REPORTS / source.name)
    print(f"Offline assets synchronized to {PUBLIC}")


if __name__ == "__main__":
    main()
