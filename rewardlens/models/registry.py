from __future__ import annotations

import json
import os
from typing import Any

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JSON_PATH = os.path.join(ROOT, "models", "model_registry.json")
YAML_PATH = os.path.join(ROOT, "models", "model_registry.yaml")


def load_registry(path: str | None = None) -> dict[str, Any]:
    json_path = path or JSON_PATH
    if json_path.endswith(".yaml") or json_path.endswith(".yml"):
        try:
            import yaml
        except ImportError as exc:
            raise RuntimeError("PyYAML required to read %s" % json_path) from exc
        with open(json_path, "r", encoding="utf-8") as handle:
            return yaml.safe_load(handle)
    if os.path.isfile(json_path):
        with open(json_path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    if os.path.isfile(YAML_PATH):
        import yaml

        with open(YAML_PATH, "r", encoding="utf-8") as handle:
            return yaml.safe_load(handle)
    raise FileNotFoundError("no model registry found")


def iter_models(registry: dict[str, Any] | None = None):
    registry = registry or load_registry()
    for rec in registry.get("models", []):
        yield rec


def get_model(model_id: str) -> dict[str, Any]:
    for rec in iter_models():
        if rec.get("model_id") == model_id:
            return rec
    raise KeyError("unknown model_id: %s" % model_id)


def primary_models(registry: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    out = []
    for rec in iter_models(registry):
        if rec.get("fast_track_primary") and rec.get("status") != "INCOMPATIBLE":
            out.append(rec)
    return out


def models_for_worker(worker: int, registry: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    out = []
    for rec in iter_models(registry):
        if rec.get("fast_track_primary") and int(rec.get("worker", -1)) == int(worker):
            if rec.get("status") != "INCOMPATIBLE":
                out.append(rec)
    return out


def models_for_shard(worker_index: int, num_workers: int, registry: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    if num_workers < 1:
        raise ValueError("num_workers must be >= 1")
    if worker_index < 0 or worker_index >= num_workers:
        raise ValueError("worker_index must be in [0, num_workers)")
    primary = primary_models(registry)
    if num_workers == 2 and all(rec.get("worker") in (0, 1) for rec in primary):
        return [rec for rec in primary if int(rec.get("worker", -1)) == int(worker_index)]
    return [rec for i, rec in enumerate(primary) if i % num_workers == worker_index]


def family_counts(registry: dict[str, Any] | None = None) -> dict[str, int]:
    counts: dict[str, int] = {}
    for rec in iter_models(registry):
        if rec.get("fast_track_primary"):
            fam = str(rec.get("family"))
            counts[fam] = counts.get(fam, 0) + 1
    return counts
