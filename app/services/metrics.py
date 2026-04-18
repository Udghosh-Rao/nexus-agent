import threading
from collections import defaultdict
from typing import Any


class MetricsStore:
    MAX_LATENCY_SAMPLES = 2000

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._counters: dict[str, int] = defaultdict(int)
        self._latency: dict[str, list[float]] = defaultdict(list)

    def inc(self, key: str, value: int = 1) -> None:
        with self._lock:
            self._counters[key] += value

    def observe_latency(self, route: str, latency_ms: float) -> None:
        with self._lock:
            bucket = self._latency[route]
            bucket.append(latency_ms)
            if len(bucket) > self.MAX_LATENCY_SAMPLES:
                del bucket[: len(bucket) - self.MAX_LATENCY_SAMPLES]

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            latency_summary = {}
            for route, values in self._latency.items():
                if not values:
                    continue
                avg_ms = sum(values) / len(values)
                p95_ms = sorted(values)[max(0, int(0.95 * len(values)) - 1)]
                latency_summary[route] = {
                    "count": len(values),
                    "avg_ms": round(avg_ms, 2),
                    "p95_ms": round(p95_ms, 2),
                }

            return {
                "counters": dict(self._counters),
                "latency_ms": latency_summary,
            }


metrics_store = MetricsStore()
