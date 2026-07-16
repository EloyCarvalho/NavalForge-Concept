"""Release-oriented repository verification without hidden validation claims."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from navalforge_core.models import Project

ROOT = Path(__file__).resolve().parents[1]


def require(path: str) -> Path:
    target = ROOT / path
    if not target.exists():
        raise RuntimeError(f"Required artifact is missing: {path}")
    return target


def main() -> None:
    required = [
        "README.md",
        "LICENSE",
        "docker-compose.yml",
        ".env.example",
        "backend/app/main.py",
        "frontend/dist/index.html",
        "frontend/dist/sw.js",
        "frontend/dist/manifest.webmanifest",
        "databases/engines/engines.json",
    ]
    for item in required:
        require(item)

    project_files = sorted((ROOT / "examples").glob("nf-demo-*.json"))
    if len(project_files) != 3:
        raise RuntimeError(f"Expected exactly 3 demo projects, found {len(project_files)}")
    for project_path in project_files:
        project = Project.model_validate_json(project_path.read_text(encoding="utf-8"))
        result_path = ROOT / "examples" / "generated" / f"{project_path.stem}.json"
        result = json.loads(require(result_path.relative_to(ROOT).as_posix()).read_text(encoding="utf-8"))
        if not result["requirements"]["mandatory_gate_passed"]:
            raise RuntimeError(f"Demo mandatory gate failed: {project.project_id}")
        for extension in ("pdf", "docx", "xlsx", "csv", "json"):
            report = ROOT / "examples" / "generated" / f"{project_path.stem}.{extension}"
            if not report.exists() or report.stat().st_size < 100:
                raise RuntimeError(f"Invalid report artifact: {report.name}")

    sw = (ROOT / "frontend" / "dist" / "sw.js").read_text(encoding="utf-8")
    if "const BUILD = []" in sw or "/assets/" not in sw:
        raise RuntimeError("Production service worker does not include hashed build assets")
    subprocess.run(
        [sys.executable, "-m", "compileall", "-q", "navalforge_core", "backend", "scripts"],
        cwd=ROOT,
        check=True,
    )
    print("Repository structure, examples, reports, PWA cache and Python syntax verified.")


if __name__ == "__main__":
    main()
