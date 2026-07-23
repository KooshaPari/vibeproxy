"""CLI: ``python -m exporter export|probe``."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from exporter.envelope import ObservationError, build_observation
from exporter.prometheus import (
    PrometheusScrapeError,
    parse_prometheus_text,
    samples_to_gauge_map,
    scrape_prometheus_url,
)

DEFAULT_LOCAL_URL = "http://127.0.0.1:9090/metrics"


def _load_metrics_text(args: argparse.Namespace) -> str:
    sources = [
        bool(args.from_prometheus_url),
        bool(args.from_metrics_file),
        bool(args.localhost),
    ]
    if sum(sources) != 1:
        raise ObservationError(
            "exactly one of --from-prometheus-url, --from-metrics-file, "
            "or --localhost is required"
        )
    if args.from_metrics_file:
        path = Path(args.from_metrics_file)
        if not path.is_file():
            raise ObservationError(f"metrics file not found: {path}")
        try:
            return path.read_text(encoding="utf-8")
        except OSError as exc:
            raise ObservationError(f"failed to read metrics file: {exc}") from exc
    url = args.from_prometheus_url or DEFAULT_LOCAL_URL
    return scrape_prometheus_url(url, timeout_s=args.timeout_s)


def _parse_labels(raw: list[str]) -> dict[str, str]:
    labels: dict[str, str] = {}
    for item in raw:
        if "=" not in item:
            raise ObservationError(
                f"invalid --label {item!r}; expected key=value"
            )
        key, value = item.split("=", 1)
        if not key:
            raise ObservationError(f"invalid --label {item!r}; empty key")
        labels[key] = value
    return labels


def _build_from_args(args: argparse.Namespace) -> dict:
    text = _load_metrics_text(args)
    samples = parse_prometheus_text(text)
    gauges = samples_to_gauge_map(samples)
    return build_observation(
        gauges,
        service=args.service,
        instance=args.instance,
        observed_at=args.observed_at,
        window_s=args.window_s,
        labels=_parse_labels(args.label) if args.label else None,
    )


def _add_source_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--from-prometheus-url",
        default="",
        help="Scrape Prometheus text exposition from this URL",
    )
    parser.add_argument(
        "--from-metrics-file",
        default="",
        help="Read Prometheus text from a local /metrics dump (offline CI)",
    )
    parser.add_argument(
        "--localhost",
        action="store_true",
        help=f"Scrape default local Prometheus ({DEFAULT_LOCAL_URL})",
    )
    parser.add_argument(
        "--timeout-s",
        type=float,
        default=5.0,
        help="HTTP scrape timeout seconds (default: 5)",
    )
    parser.add_argument("--service", default="vibeproxy")
    parser.add_argument("--instance", default="local")
    parser.add_argument(
        "--observed-at",
        default="",
        help="ISO-8601 UTC stamp (default: now)",
    )
    parser.add_argument("--window-s", type=int, default=60)
    parser.add_argument(
        "--label",
        action="append",
        default=[],
        help="Optional envelope label key=value (repeatable)",
    )


def cmd_export(args: argparse.Namespace) -> int:
    try:
        observation = _build_from_args(args)
    except (ObservationError, PrometheusScrapeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    payload = json.dumps(observation, indent=2, sort_keys=True) + "\n"
    if args.output:
        out = Path(args.output)
        try:
            out.write_text(payload, encoding="utf-8")
        except OSError as exc:
            print(f"ERROR: failed to write {out}: {exc}", file=sys.stderr)
            return 2
        print(f"wrote {out}", file=sys.stderr)
    else:
        sys.stdout.write(payload)
    return 0


def cmd_probe(args: argparse.Namespace) -> int:
    """Exit 0 when a complete envelope can be built; else 2 with missing keys."""
    try:
        observation = _build_from_args(args)
    except (ObservationError, PrometheusScrapeError) as exc:
        print(f"PROBE_FAIL: {exc}", file=sys.stderr)
        return 2
    print(
        json.dumps(
            {
                "ok": True,
                "schema": observation["schema"],
                "service": observation["service"],
                "instance": observation["instance"],
                "observed_at": observation["observed_at"],
            },
            sort_keys=True,
        )
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m exporter",
        description=(
            "Export vibeproxy.monitoring.v1 JSON from Prometheus /metrics "
            "(URL or file). Loud-fails when required serving/resource metrics "
            "are missing."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    export_p = sub.add_parser(
        "export",
        help="Emit vibeproxy.monitoring.v1 JSON to stdout or --output",
    )
    _add_source_args(export_p)
    export_p.add_argument(
        "--output",
        "-o",
        default="",
        help="Write JSON to this path instead of stdout",
    )
    export_p.set_defaults(func=cmd_export)

    probe_p = sub.add_parser(
        "probe",
        help="Validate that required metrics resolve; exit 0/2",
    )
    _add_source_args(probe_p)
    probe_p.set_defaults(func=cmd_probe)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.observed_at == "":
        args.observed_at = None
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
