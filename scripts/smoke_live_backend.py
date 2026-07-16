"""Exercise the public Render API and its production CORS contract.

This script deliberately uses only the Python standard library so it can run
from a clean GitHub Actions runner.  It never prints database credentials.
"""

from __future__ import annotations

import json
import os
import sys
import time
import tomllib
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import uuid4

API_URL = os.environ.get(
    "LIVE_API_URL", "https://navalforge-concept-api.onrender.com"
).rstrip("/")
PWA_ORIGIN = os.environ.get(
    "LIVE_PWA_ORIGIN", "https://navalforgeconcept.pages.dev"
).rstrip("/")
PROJECT_PATH = Path(__file__).resolve().parents[1] / "examples" / "nf-demo-service-7m.json"
PYPROJECT_PATH = Path(__file__).resolve().parents[1] / "pyproject.toml"
VERIFY_DEPLOYED_VERSION = os.environ.get("VERIFY_DEPLOYED_VERSION", "false").lower() == "true"


def expected_app_version() -> str:
    with PYPROJECT_PATH.open("rb") as file:
        return str(tomllib.load(file)["project"]["version"])


def request_json(request: Request, timeout: int = 300) -> tuple[Any, Any]:
    with urlopen(request, timeout=timeout) as response:  # noqa: S310 - fixed HTTPS URL
        content_type = response.headers.get("content-type", "")
        if "json" not in content_type:
            raise RuntimeError(f"Expected JSON, received {content_type!r}")
        return json.load(response), response.headers


def wait_until_ready() -> dict[str, Any]:
    last_error: Exception | None = None
    expected_version = expected_app_version()
    for attempt in range(1, 31):
        try:
            payload, _ = request_json(Request(f"{API_URL}/ready"), timeout=30)
            version_matches = payload.get("version") == expected_version
            if payload.get("status") == "healthy" and (
                not VERIFY_DEPLOYED_VERSION or version_matches
            ):
                return payload
            last_error = RuntimeError(
                f"Readiness has not reached app {expected_version}: {payload!r}"
            )
        except (HTTPError, URLError, TimeoutError, RuntimeError) as exc:
            last_error = exc
        print(f"Readiness attempt {attempt}/30 failed; retrying in 10 seconds")
        time.sleep(10)
    raise RuntimeError(f"API did not become ready: {last_error}")


def verify_preflight() -> None:
    request = Request(
        f"{API_URL}/api/v1/evaluate",
        method="OPTIONS",
        headers={
            "Origin": PWA_ORIGIN,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    with urlopen(request, timeout=60) as response:  # noqa: S310 - fixed HTTPS URL
        allowed_origin = response.headers.get("access-control-allow-origin")
        if allowed_origin != PWA_ORIGIN:
            raise RuntimeError(
                f"CORS rejected PWA origin: expected {PWA_ORIGIN!r}, got {allowed_origin!r}"
            )


def evaluate_project() -> dict[str, Any]:
    project = json.loads(PROJECT_PATH.read_text(encoding="utf-8"))
    body = json.dumps({"project": project, "include_variants": True}).encode()
    request = Request(
        f"{API_URL}/api/v1/evaluate",
        data=body,
        method="POST",
        headers={"Content-Type": "application/json", "Origin": PWA_ORIGIN},
    )
    result, headers = request_json(request)
    if headers.get("access-control-allow-origin") != PWA_ORIGIN:
        raise RuntimeError("Evaluation response is missing the expected CORS header")
    if result.get("project_id") != project["project_id"]:
        raise RuntimeError("Evaluation returned the wrong project identifier")
    for required in ("results", "requirements", "indicators", "traceability"):
        if not result.get(required):
            raise RuntimeError(f"Evaluation is missing non-empty {required!r}")
    alternatives = result.get("selected_alternatives", {})
    if not all(alternatives.get(name) for name in ("eco", "balanced", "performance")):
        raise RuntimeError("Evaluation did not produce all three required alternatives")
    return result


def verify_revision_persistence() -> dict[str, Any]:
    """Create, revise and remove a synthetic project in the live Neon database."""

    project = json.loads(PROJECT_PATH.read_text(encoding="utf-8"))
    project["project_id"] = f"NF-SMOKE-{uuid4().hex[:12].upper()}"
    project["name"] = "Temporary automated persistence smoke"
    created = False
    try:
        create_body = json.dumps(
            {"project": project, "change_summary": "Automated live smoke P1"}
        ).encode()
        created_payload, _ = request_json(
            Request(
                f"{API_URL}/api/v1/projects",
                data=create_body,
                method="POST",
                headers={"Content-Type": "application/json", "Origin": PWA_ORIGIN},
            )
        )
        created = True
        if created_payload.get("project", {}).get("revision") != "P1":
            raise RuntimeError("Project creation did not preserve revision P1")

        revised_project = created_payload["project"]
        revised_project["description"] = "Revision persistence smoke update"
        revision_body = json.dumps(
            {
                "project": revised_project,
                "expected_revision": "P1",
                "change_summary": "Automated live smoke P2",
            }
        ).encode()
        revised_payload, _ = request_json(
            Request(
                f"{API_URL}/api/v1/projects/{project['project_id']}/revisions",
                data=revision_body,
                method="POST",
                headers={"Content-Type": "application/json", "Origin": PWA_ORIGIN},
            )
        )
        if revised_payload.get("project", {}).get("revision") != "P2":
            raise RuntimeError("Project update did not increment revision to P2")

        history, _ = request_json(
            Request(f"{API_URL}/api/v1/projects/{project['project_id']}/revisions")
        )
        labels = {item.get("revision") for item in history}
        if labels != {"P1", "P2"}:
            raise RuntimeError(f"Unexpected revision history: {labels!r}")
        return {"project_id": project["project_id"], "revisions": sorted(labels)}
    finally:
        if created:
            request = Request(
                f"{API_URL}/api/v1/projects/{project['project_id']}",
                method="DELETE",
                headers={"Origin": PWA_ORIGIN},
            )
            with urlopen(request, timeout=60) as response:  # noqa: S310 - fixed HTTPS URL
                if response.status != 204:
                    raise RuntimeError(f"Smoke cleanup returned HTTP {response.status}")


def main() -> int:
    ready = wait_until_ready()
    verify_preflight()
    result = evaluate_project()
    persistence = verify_revision_persistence() if VERIFY_DEPLOYED_VERSION else None
    summary = {
        "api": API_URL,
        "version": ready.get("version"),
        "expected_version": expected_app_version(),
        "algorithm_version": ready.get("algorithm_version"),
        "project_id": result["project_id"],
        "status": result["status"],
        "variants": len(result.get("variants", [])),
        "mandatory_gate_passed": result["requirements"]["mandatory_gate_passed"],
        "persistence": persistence,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # provide a concise CI error without suppressing failure
        print(f"Live backend smoke failed: {exc}", file=sys.stderr)
        raise
