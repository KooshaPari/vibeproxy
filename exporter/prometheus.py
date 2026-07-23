"""Prometheus text exposition scrape + parse (stdlib only)."""

from __future__ import annotations

import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Mapping

# metric_name{labels} value [timestamp]
_SAMPLE_RE = re.compile(
    r"^(?P<name>[a-zA-Z_:][a-zA-Z0-9_:]*)"
    r"(?:\{(?P<labels>[^}]*)\})?"
    r"\s+(?P<value>[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?|[+-]?Inf|NaN)"
    r"(?:\s+\d+)?\s*$"
)


@dataclass(frozen=True)
class Sample:
    name: str
    labels: Mapping[str, str]
    value: float


class PrometheusScrapeError(RuntimeError):
    """Raised when Prometheus text cannot be fetched or parsed."""


def _parse_labels(raw: str | None) -> dict[str, str]:
    if not raw:
        return {}
    labels: dict[str, str] = {}
    # label="value", with escaped quotes
    for match in re.finditer(
        r'([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*"((?:\\.|[^"\\])*)"',
        raw,
    ):
        key, value = match.group(1), match.group(2)
        labels[key] = value.replace('\\"', '"').replace("\\\\", "\\")
    return labels


def parse_prometheus_text(text: str) -> list[Sample]:
    """Parse Prometheus text exposition into samples.

    Comments (#) and TYPE/HELP lines are ignored. Histogram/summary quantiles
    are kept as labeled samples; the exporter mapping selects by name aliases.
    """
    samples: list[Sample] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        match = _SAMPLE_RE.match(stripped)
        if not match:
            raise PrometheusScrapeError(
                f"invalid prometheus sample at line {lineno}: {stripped!r}"
            )
        raw_value = match.group("value")
        if raw_value in {"NaN", "+Inf", "-Inf", "Inf"}:
            raise PrometheusScrapeError(
                f"non-finite prometheus value at line {lineno}: {raw_value}"
            )
        samples.append(
            Sample(
                name=match.group("name"),
                labels=_parse_labels(match.group("labels")),
                value=float(raw_value),
            )
        )
    return samples


def scrape_prometheus_url(url: str, timeout_s: float = 5.0) -> str:
    """GET Prometheus text from ``url``. Loud-fail on HTTP/network errors."""
    try:
        request = urllib.request.Request(
            url,
            headers={"Accept": "text/plain; version=0.0.4"},
            method="GET",
        )
        with urllib.request.urlopen(request, timeout=timeout_s) as response:
            status = getattr(response, "status", None) or response.getcode()
            if status != 200:
                raise PrometheusScrapeError(
                    f"prometheus scrape failed: HTTP {status} for {url}"
                )
            body = response.read()
    except urllib.error.HTTPError as exc:
        raise PrometheusScrapeError(
            f"prometheus scrape failed: HTTP {exc.code} for {url}"
        ) from exc
    except urllib.error.URLError as exc:
        raise PrometheusScrapeError(
            f"prometheus scrape failed for {url}: {exc.reason}"
        ) from exc
    except TimeoutError as exc:
        raise PrometheusScrapeError(
            f"prometheus scrape timed out after {timeout_s}s for {url}"
        ) from exc
    try:
        return body.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise PrometheusScrapeError(
            f"prometheus body is not utf-8 for {url}: {exc}"
        ) from exc


def samples_to_gauge_map(samples: list[Sample]) -> dict[str, float]:
    """Collapse samples to name → value for unlabeled gauges.

    If multiple samples share a name, prefer unlabeled; else first sample wins
    (deterministic by input order). Quantile-labeled series remain accessible
    only via exact name aliases used by the envelope builder.
    """
    by_name: dict[str, float] = {}
    unlabeled: dict[str, float] = {}
    for sample in samples:
        if not sample.labels:
            unlabeled[sample.name] = sample.value
        elif sample.name not in by_name:
            by_name[sample.name] = sample.value
    merged = dict(by_name)
    merged.update(unlabeled)
    return merged
