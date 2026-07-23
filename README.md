# vibeproxy-monitoring-unified

Unified monitoring configuration for VibeProxy services. This repository is the
governance and specification home for shared VibeProxy observability assets.

## Status

Governance/spec scaffolding plus a minimal **live exporter** (`exporter/`) that
emits `vibeproxy.monitoring.v1` JSON from Prometheus text (`/metrics` URL or
file). Dashboards and alert rules are still out of scope.

## Scope

`vibeproxy-monitoring-unified` is intended to standardize monitoring and health
signals across VibeProxy services:

- Shared monitoring configuration and dashboard ownership.
- Alert definitions for VibeProxy service health and dependency failures.
- Consistent liveness, readiness, and startup semantics for service probes.
- Prometheus and Grafana surfaces for probe latency, availability, and error
  budget tracking.
- Documentation for routing repo-specific findings into the local worklog.

## Current Layout

| Path | Purpose |
|------|---------|
| `exporter/` | Stdlib Python exporter → `vibeproxy.monitoring.v1` |
| `tests/` | Offline smoke tests (Prometheus fixture → envelope) |
| `SPEC.md` | Specification: scope and intended contents |
| `AGENTS.md` | Agent governance |
| `CLAUDE.md` | Claude Code project instructions |
| `FUNCTIONAL_REQUIREMENTS.md` | Functional requirements tracker |
| `docs/worklogs/README.md` | Canonical worklog index |
| `docs/worklogs/worklog.md` | Detailed work audit log |

## Quick Start

```bash
git clone https://github.com/KooshaPari/vibeproxy-monitoring-unified.git
cd vibeproxy-monitoring-unified
mise install
pre-commit install
python -m unittest discover -s tests -v
```

## Exporter (`vibeproxy.monitoring.v1`)

Scrapes Prometheus text exposition and builds the JSON envelope expected by
pheno-harness `eval.observability.vibeproxy_adapter`. **Missing required
serving/resource metrics fail loud** (exit 2 + missing-key list). No silent
defaults.

### Commands

```bash
# Offline / CI: synthesize from a /metrics dump
python -m exporter export --from-metrics-file tests/fixtures/prometheus_metrics.txt

# Live scrape (default local Prometheus)
python -m exporter export --localhost
python -m exporter export --from-prometheus-url http://127.0.0.1:9090/metrics

# Probe (exit 0 if envelope can be built; else 2)
python -m exporter probe --from-metrics-file tests/fixtures/prometheus_metrics.txt
```

Write to a file with `-o observation.json`. Optional: `--service`, `--instance`,
`--observed-at`, `--window-s`, `--label key=value`.

### Pipe into pheno-harness

```bash
# From this repo: emit observation JSON
python -m exporter export \
  --from-prometheus-url http://127.0.0.1:9090/metrics \
  --instance "$(hostname)" \
  -o /tmp/vibeproxy-observation.json

# In pheno-harness (adapter + ingest CLI from AgilePlus #75 / PR vibeproxy→garden):
python scripts/ingest_vibeproxy_observation.py \
  --input /tmp/vibeproxy-observation.json

# Dry-run prints mapped garden serving metrics; add --append to ledger-observe.
```

One-liner pipe (stdout → ingest via temp file is preferred; ingest takes a path):

```bash
python -m exporter export --from-metrics-file tests/fixtures/prometheus_metrics.txt \
  -o /tmp/vibeproxy-observation.json \
  && python /path/to/pheno-harness/scripts/ingest_vibeproxy_observation.py \
       -i /tmp/vibeproxy-observation.json
```

Schema compatibility: exported `serving` / `resources` keys use adapter aliases
(`ttft_p50_ms`, `itl_p50_ms`, `tokens_per_s`, `queue_latency_ms`,
`ctx_cache_hit_rate`, `kv_cached_tokens`, `worker_crashes`, `cpu_util`,
`ram_used_mb`, `vram_used_mb`, `disk_*`, `net_*`).

Required Prometheus gauge names (any alias per garden key) are documented in
`exporter/envelope.py` (`_PROM_ALIASES`).

## Future Implementation Targets

Still pending (not in this slice):

- Dashboard definitions for service health and latency.
- Alert rules for unhealthy probes, dependency degradation, and error budgets.
- Example Kubernetes and Docker health-check configuration.
- Prometheus recording rules for normalized probe metrics.
- Wiring OmniRoute / cliproxyapi to emit the `vibeproxy_*` gauges.

## Governance

Record repo-specific findings in `docs/worklogs/worklog.md`. Use parent
Phenotype governance and worklog surfaces only for cross-repo aggregation or
org-level decisions.

All future monitoring assets should include:

- Clear owning service or platform surface.
- Test or validation command where applicable.
- Alert severity and routing assumptions.
- Rollback or disablement guidance for noisy checks.

## Links

- Canonical repo: https://github.com/KooshaPari/vibeproxy-monitoring-unified
