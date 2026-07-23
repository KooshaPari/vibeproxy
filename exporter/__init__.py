"""VibeProxy monitoring exporter → ``vibeproxy.monitoring.v1`` JSON.

Scrapes Prometheus text exposition (URL or file) and emits the envelope
expected by pheno-harness ``eval.observability.vibeproxy_adapter``.

Loud-fail: missing required serving/resource metrics abort with a non-zero
exit and a clear missing-key list. No silent defaults.
"""

from __future__ import annotations

from exporter.envelope import SCHEMA_V1, build_observation, ObservationError
from exporter.prometheus import parse_prometheus_text, scrape_prometheus_url

__all__ = [
    "SCHEMA_V1",
    "ObservationError",
    "build_observation",
    "parse_prometheus_text",
    "scrape_prometheus_url",
]

__version__ = "0.1.0"
