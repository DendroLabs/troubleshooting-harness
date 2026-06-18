#!/usr/bin/env python3
"""Validate every TSH JSON data file against its schema.

Cross-file ``$ref`` resolution (protocol.schema.json and definition.schema.json
both reference applicability.schema.json) is handled with the ``referencing``
registry. Exit code is non-zero if any file fails, so this is CI-safe.

Usage:
    python tools/validate/validate_all.py            # validate everything
    python tools/validate/validate_all.py protocols  # just one data subdir
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA = REPO_ROOT / "data"
SCHEMA_DIR = DATA / "_schema"

# Maps a data subdirectory to the schema $id its files must validate against.
DIR_SCHEMA = {
    "protocols": "protocol.schema.json",
    "definitions": "definition.schema.json",
    "diagnostics": "diagnostic-tree.schema.json",
    "procedures": "procedure.schema.json",
    "human-errors": "human-error.schema.json",
    "platforms": "platform.schema.json",
    "concepts": "concept.schema.json",
    "best-practices": "best-practice.schema.json",
    "interpretation-rules": "interpretation-rule.schema.json",
}


def build_registry() -> Registry:
    """Load all schema files into a referencing registry keyed by their $id."""
    resources = []
    for path in sorted(SCHEMA_DIR.glob("*.schema.json")):
        contents = json.loads(path.read_text())
        resource = Resource.from_contents(contents, default_specification=DRAFT202012)
        resources.append((contents["$id"], resource))
    return Registry().with_resources(resources)


def iter_data_files(only: str | None):
    for subdir, schema_id in DIR_SCHEMA.items():
        if only and subdir != only:
            continue
        root = DATA / subdir
        if not root.exists():
            continue
        for path in sorted(root.rglob("*.json")):
            # Index / cross-reference files are not schema-validated here.
            if path.name.startswith("_"):
                continue
            yield path, schema_id


def main() -> int:
    only = sys.argv[1] if len(sys.argv) > 1 else None
    registry = build_registry()
    validators = {
        schema_id: Draft202012Validator(
            registry.get_or_retrieve(schema_id).value.contents, registry=registry
        )
        for schema_id in set(DIR_SCHEMA.values())
        if (SCHEMA_DIR / schema_id).exists()
    }

    total = ok = 0
    failures: list[str] = []
    for path, schema_id in iter_data_files(only):
        total += 1
        rel = path.relative_to(REPO_ROOT)
        validator = validators.get(schema_id)
        if validator is None:
            failures.append(f"{rel}: no schema loaded for {schema_id}")
            continue
        try:
            data = json.loads(path.read_text())
        except json.JSONDecodeError as exc:
            failures.append(f"{rel}: invalid JSON — {exc}")
            continue
        errors = sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path))
        if errors:
            for err in errors:
                loc = "/".join(str(p) for p in err.absolute_path) or "<root>"
                failures.append(f"{rel}: at {loc}: {err.message}")
        else:
            ok += 1

    print(f"Validated {ok}/{total} files against {len(validators)} schema(s).")
    if failures:
        print(f"\n{len(failures)} validation error(s):", file=sys.stderr)
        for line in failures:
            print(f"  FAIL {line}", file=sys.stderr)
        return 1
    print("All files valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
