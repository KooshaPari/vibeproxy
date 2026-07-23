"""Build ``vibeproxy.monitoring.v1`` observation envelopes.

Metric name aliases mirror pheno-harness
``eval.observability.vibeproxy_adapter`` (garden serving keys).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

SCHEMA_V1 = "vibeproxy.monitoring.v1"

# Prometheus metric name aliases → (section, json_key). First hit wins.
# Section is "serving" or "resources". json_key is a garden-accepted alias.
_PROM_ALIASES: dict[str, tuple[tuple[str, ...], str, str]] = {
    # garden_key: (prom names..., section, envelope_key)
    "ttft_ms": (
        (
            "vibeproxy_ttft_ms",
            "vibeproxy_ttft_p50_ms",
            "vibeproxy_time_to_first_token_ms",
            "ttft_ms",
            "ttft_p50_ms",
        ),
        "serving",
        "ttft_p50_ms",
    ),
    "inter_token_latency_ms": (
        (
            "vibeproxy_inter_token_latency_ms",
            "vibeproxy_itl_ms",
            "vibeproxy_itl_p50_ms",
            "itl_ms",
            "itl_p50_ms",
            "inter_token_latency_ms",
        ),
        "serving",
        "itl_p50_ms",
    ),
    "aggregate_tokens_per_s": (
        (
            "vibeproxy_aggregate_tokens_per_s",
            "vibeproxy_tokens_per_s",
            "vibeproxy_tps",
            "tokens_per_s",
            "tps",
            "aggregate_tokens_per_s",
        ),
        "serving",
        "tokens_per_s",
    ),
    "queue_wait_ms": (
        (
            "vibeproxy_queue_wait_ms",
            "vibeproxy_queue_latency_ms",
            "queue_wait_ms",
            "queue_latency_ms",
        ),
        "serving",
        "queue_latency_ms",
    ),
    "prefix_cache_hit_rate": (
        (
            "vibeproxy_prefix_cache_hit_rate",
            "vibeproxy_ctx_cache_hit_rate",
            "vibeproxy_cache_hit_rate",
            "prefix_cache_hit_rate",
            "ctx_cache_hit_rate",
            "cache_hit_rate",
        ),
        "serving",
        "ctx_cache_hit_rate",
    ),
    "kv_cache_tokens": (
        (
            "vibeproxy_kv_cache_tokens",
            "vibeproxy_kv_cached_tokens",
            "kv_cache_tokens",
            "kv_cached_tokens",
        ),
        "serving",
        "kv_cached_tokens",
    ),
    "crash_count": (
        (
            "vibeproxy_crash_count",
            "vibeproxy_worker_crashes",
            "crash_count",
            "worker_crashes",
        ),
        "serving",
        "worker_crashes",
    ),
    "cpu_pct": (
        (
            "vibeproxy_cpu_pct",
            "vibeproxy_cpu_util",
            "cpu_pct",
            "cpu_util",
        ),
        "resources",
        "cpu_util",
    ),
    "ram_mb": (
        (
            "vibeproxy_ram_mb",
            "vibeproxy_ram_used_mb",
            "ram_mb",
            "ram_used_mb",
        ),
        "resources",
        "ram_used_mb",
    ),
    "vram_mb": (
        (
            "vibeproxy_vram_mb",
            "vibeproxy_vram_used_mb",
            "vram_mb",
            "vram_used_mb",
        ),
        "resources",
        "vram_used_mb",
    ),
    "disk_read_mb_s": (
        ("vibeproxy_disk_read_mb_s", "disk_read_mb_s"),
        "resources",
        "disk_read_mb_s",
    ),
    "disk_write_mb_s": (
        ("vibeproxy_disk_write_mb_s", "disk_write_mb_s"),
        "resources",
        "disk_write_mb_s",
    ),
    "network_rx_mb_s": (
        (
            "vibeproxy_network_rx_mb_s",
            "vibeproxy_net_rx_mb_s",
            "network_rx_mb_s",
            "net_rx_mb_s",
        ),
        "resources",
        "net_rx_mb_s",
    ),
    "network_tx_mb_s": (
        (
            "vibeproxy_network_tx_mb_s",
            "vibeproxy_net_tx_mb_s",
            "network_tx_mb_s",
            "net_tx_mb_s",
        ),
        "resources",
        "net_tx_mb_s",
    ),
}

REQUIRED_GARDEN_KEYS: tuple[str, ...] = tuple(_PROM_ALIASES.keys())


class ObservationError(ValueError):
    """Raised when required metrics cannot be resolved into an envelope."""


def _coerce_value(garden_key: str, value: float) -> float | int:
    if garden_key in {"crash_count", "kv_cache_tokens"}:
        if not float(value).is_integer():
            raise ObservationError(
                f"metric {garden_key!r} must be an integer count, got {value}"
            )
        return int(value)
    return float(value)


def resolve_metrics(gauges: Mapping[str, float]) -> dict[str, dict[str, float | int]]:
    """Map Prometheus gauges → serving/resources objects using aliases."""
    serving: dict[str, float | int] = {}
    resources: dict[str, float | int] = {}
    missing: list[str] = []

    for garden_key, (names, section, envelope_key) in _PROM_ALIASES.items():
        found: float | None = None
        for name in names:
            if name in gauges:
                found = float(gauges[name])
                break
        if found is None:
            missing.append(garden_key)
            continue
        coerced = _coerce_value(garden_key, found)
        if section == "serving":
            serving[envelope_key] = coerced
        else:
            resources[envelope_key] = coerced

    if missing:
        raise ObservationError(
            "missing required vibeproxy metrics after alias resolution: "
            + ", ".join(missing)
        )
    return {"serving": serving, "resources": resources}


def _optional_probes(gauges: Mapping[str, float]) -> dict[str, Any] | None:
    liveness_ok = gauges.get("vibeproxy_probe_liveness_ok")
    readiness_ok = gauges.get("vibeproxy_probe_readiness_ok")
    if liveness_ok is None and readiness_ok is None:
        return None
    probes: dict[str, Any] = {}
    if liveness_ok is not None:
        probes["liveness"] = {
            "ok": bool(liveness_ok),
            "latency_ms": float(gauges.get("vibeproxy_probe_liveness_latency_ms", 0.0)),
        }
    if readiness_ok is not None:
        probes["readiness"] = {
            "ok": bool(readiness_ok),
            "latency_ms": float(
                gauges.get("vibeproxy_probe_readiness_latency_ms", 0.0)
            ),
        }
    return probes


def build_observation(
    gauges: Mapping[str, float],
    *,
    service: str = "vibeproxy",
    instance: str = "local",
    observed_at: str | None = None,
    window_s: int = 60,
    labels: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Construct a validated ``vibeproxy.monitoring.v1`` observation."""
    if not service.strip():
        raise ObservationError("service must be a non-empty string")
    if not instance.strip():
        raise ObservationError("instance must be a non-empty string")

    resolved = resolve_metrics(gauges)
    stamp = observed_at or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    observation: dict[str, Any] = {
        "schema": SCHEMA_V1,
        "observed_at": stamp,
        "service": service,
        "instance": instance,
        "window_s": int(window_s),
        "serving": resolved["serving"],
        "resources": resolved["resources"],
    }
    if labels:
        observation["labels"] = dict(labels)
    probes = _optional_probes(gauges)
    if probes is not None:
        observation["probes"] = probes
    return observation
