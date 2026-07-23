"""Smoke + contract tests for the vibeproxy.monitoring.v1 exporter."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "prometheus_metrics.txt"

# Keys the pheno-harness adapter requires after alias resolution.
GARDEN_KEYS = (
    "ttft_ms",
    "inter_token_latency_ms",
    "aggregate_tokens_per_s",
    "queue_wait_ms",
    "prefix_cache_hit_rate",
    "kv_cache_tokens",
    "cpu_pct",
    "ram_mb",
    "vram_mb",
    "disk_read_mb_s",
    "disk_write_mb_s",
    "network_rx_mb_s",
    "network_tx_mb_s",
    "crash_count",
)


class ExporterSmokeTests(unittest.TestCase):
    def test_export_from_metrics_file(self) -> None:
        proc = subprocess.run(
            [
                sys.executable,
                "-m",
                "exporter",
                "export",
                "--from-metrics-file",
                str(FIXTURE),
                "--service",
                "vibeproxy",
                "--instance",
                "local-fixture-1",
                "--observed-at",
                "2026-07-22T18:00:00Z",
                "--label",
                "env=fixture",
                "--label",
                "lane=serving",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["schema"], "vibeproxy.monitoring.v1")
        self.assertEqual(payload["service"], "vibeproxy")
        self.assertEqual(payload["instance"], "local-fixture-1")
        self.assertEqual(payload["observed_at"], "2026-07-22T18:00:00Z")
        self.assertEqual(payload["serving"]["ttft_p50_ms"], 118.5)
        self.assertEqual(payload["serving"]["itl_p50_ms"], 14.2)
        self.assertEqual(payload["serving"]["tokens_per_s"], 72.0)
        self.assertEqual(payload["serving"]["worker_crashes"], 0)
        self.assertEqual(payload["resources"]["cpu_util"], 37.5)
        self.assertEqual(payload["resources"]["ram_used_mb"], 6144)
        self.assertTrue(payload["probes"]["liveness"]["ok"])

    def test_probe_ok(self) -> None:
        proc = subprocess.run(
            [
                sys.executable,
                "-m",
                "exporter",
                "probe",
                "--from-metrics-file",
                str(FIXTURE),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        body = json.loads(proc.stdout)
        self.assertTrue(body["ok"])

    def test_loud_fail_missing_metrics(self) -> None:
        with tempfile.NamedTemporaryFile(
            "w", suffix=".txt", delete=False, encoding="utf-8"
        ) as handle:
            handle.write("unrelated_metric 1\n")
            path = Path(handle.name)
        try:
            proc = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "exporter",
                    "export",
                    "--from-metrics-file",
                    str(path),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
        finally:
            path.unlink(missing_ok=True)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("missing required vibeproxy metrics", proc.stderr)
        for key in ("ttft_ms", "cpu_pct", "crash_count"):
            self.assertIn(key, proc.stderr)

    def test_envelope_maps_to_garden_aliases(self) -> None:
        """Ensure exported keys are ones the pheno-harness adapter accepts."""
        from exporter.envelope import build_observation
        from exporter.prometheus import parse_prometheus_text, samples_to_gauge_map

        gauges = samples_to_gauge_map(
            parse_prometheus_text(FIXTURE.read_text(encoding="utf-8"))
        )
        observation = build_observation(
            gauges,
            service="vibeproxy",
            instance="t",
            observed_at="2026-07-22T18:00:00Z",
        )
        # Adapter alias resolution (duplicated here to avoid cross-repo import).
        alias_map = {
            "ttft_ms": ("ttft_ms", "ttft_p50_ms", "time_to_first_token_ms"),
            "inter_token_latency_ms": (
                "inter_token_latency_ms",
                "itl_ms",
                "itl_p50_ms",
            ),
            "aggregate_tokens_per_s": (
                "aggregate_tokens_per_s",
                "tokens_per_s",
                "tps",
            ),
            "queue_wait_ms": ("queue_wait_ms", "queue_latency_ms"),
            "prefix_cache_hit_rate": (
                "prefix_cache_hit_rate",
                "ctx_cache_hit_rate",
                "cache_hit_rate",
            ),
            "kv_cache_tokens": ("kv_cache_tokens", "kv_cached_tokens"),
            "crash_count": ("crash_count", "worker_crashes"),
            "cpu_pct": ("cpu_pct", "cpu_util"),
            "ram_mb": ("ram_mb", "ram_used_mb"),
            "vram_mb": ("vram_mb", "vram_used_mb"),
            "disk_read_mb_s": ("disk_read_mb_s",),
            "disk_write_mb_s": ("disk_write_mb_s",),
            "network_rx_mb_s": ("network_rx_mb_s", "net_rx_mb_s"),
            "network_tx_mb_s": ("network_tx_mb_s", "net_tx_mb_s"),
        }
        sections = {
            "serving": observation["serving"],
            "resources": observation["resources"],
        }
        for garden_key in GARDEN_KEYS:
            aliases = alias_map[garden_key]
            section = "resources" if garden_key in {
                "cpu_pct",
                "ram_mb",
                "vram_mb",
                "disk_read_mb_s",
                "disk_write_mb_s",
                "network_rx_mb_s",
                "network_tx_mb_s",
            } else "serving"
            found = None
            for alias in aliases:
                if alias in sections[section]:
                    found = sections[section][alias]
                    break
            self.assertIsNotNone(
                found, f"garden key {garden_key} unresolved in exported envelope"
            )


if __name__ == "__main__":
    unittest.main()
