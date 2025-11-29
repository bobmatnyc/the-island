"""
Performance Monitoring and Metrics

Design Decision: Lightweight in-memory metrics collection
Rationale:
- Track API endpoint performance for optimization
- Identify slow operations and bottlenecks
- No external dependencies (InfluxDB, Prometheus, etc.)
- Simple JSON export for analysis

Trade-offs:
- Memory: ~1MB for 10K requests vs. persistent DB
- Persistence: Metrics lost on restart vs. long-term storage
- Complexity: Simple aggregation vs. full monitoring stack

Performance Target:
- Metric recording: <0.1ms overhead
- Aggregation: <1ms for stats calculation
- Memory: <10MB for 24hrs of metrics

Alternatives Considered:
1. Prometheus: Rejected - overkill for single-server deployment
2. StatsD: Rejected - requires additional daemon
3. CloudWatch/DataDog: Rejected - vendor lock-in and cost
"""

import time
import logging
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Callable, Any
from functools import wraps
import statistics

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """
    Single performance measurement.

    Attributes:
        endpoint: API endpoint or operation name
        duration_ms: Operation duration in milliseconds
        timestamp: Unix timestamp
        status: Success/failure status
        cache_hit: Whether cache was used
    """
    endpoint: str
    duration_ms: float
    timestamp: float
    status: str = "success"
    cache_hit: bool = False


class PerformanceMonitor:
    """
    Lightweight performance monitoring for API operations.

    Usage:
        monitor = PerformanceMonitor()

        # Manual tracking
        start = time.time()
        # ... operation ...
        monitor.record("entity_detection", time.time() - start)

        # Decorator
        @monitor.track("similarity_search")
        def find_similar(doc_id):
            # ... implementation ...

        # Get stats
        stats = monitor.get_stats()

    Performance:
        - Recording: O(1) amortized
        - Stats calculation: O(n) where n = sample size
        - Memory: O(window_size) per endpoint
    """

    def __init__(self, window_size: int = 1000):
        """
        Initialize performance monitor.

        Args:
            window_size: Number of recent measurements to keep per endpoint (default: 1000)
        """
        self.window_size = window_size
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=window_size))
        self.total_requests = 0

    def record(
        self,
        endpoint: str,
        duration_ms: float,
        status: str = "success",
        cache_hit: bool = False
    ):
        """
        Record a performance measurement.

        Args:
            endpoint: Endpoint or operation name
            duration_ms: Duration in milliseconds
            status: "success" or "error"
            cache_hit: Whether cache was used

        Example:
            >>> monitor = PerformanceMonitor()
            >>> start = time.time()
            >>> # ... operation ...
            >>> monitor.record("entity_detection", (time.time() - start) * 1000)
        """
        metric = PerformanceMetric(
            endpoint=endpoint,
            duration_ms=duration_ms,
            timestamp=time.time(),
            status=status,
            cache_hit=cache_hit
        )

        self.metrics[endpoint].append(metric)
        self.total_requests += 1

    def track(self, endpoint: str, cache_aware: bool = False):
        """
        Decorator for automatic performance tracking.

        Args:
            endpoint: Name to track this operation under
            cache_aware: Whether to detect cache hits from return value

        Returns:
            Decorated function that records performance metrics

        Example:
            >>> monitor = PerformanceMonitor()
            >>> @monitor.track("detect_entities")
            >>> def detect_entities(text):
            >>>     # ... implementation ...
            >>>     return entities

        Cache-aware example:
            >>> @monitor.track("search", cache_aware=True)
            >>> def search(query):
            >>>     # Return (results, cache_hit)
            >>>     return results, True  # cache hit
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                start = time.time()
                status = "success"
                cache_hit = False

                try:
                    result = func(*args, **kwargs)

                    # Detect cache hit from return value if cache_aware
                    if cache_aware and isinstance(result, tuple) and len(result) == 2:
                        actual_result, cache_hit = result
                        return actual_result

                    return result

                except Exception as e:
                    status = "error"
                    raise

                finally:
                    duration_ms = (time.time() - start) * 1000
                    self.record(endpoint, duration_ms, status, cache_hit)

            return wrapper
        return decorator

    def get_stats(self, endpoint: Optional[str] = None) -> Dict[str, Any]:
        """
        Get performance statistics.

        Args:
            endpoint: Specific endpoint to get stats for (None = all)

        Returns:
            Dictionary with statistics:
            - count: Total measurements
            - mean_ms: Average duration
            - median_ms: Median duration
            - p95_ms: 95th percentile
            - p99_ms: 99th percentile
            - min_ms: Minimum duration
            - max_ms: Maximum duration
            - cache_hit_rate: Percentage of cache hits
            - error_rate: Percentage of errors

        Example:
            >>> stats = monitor.get_stats("entity_detection")
            >>> print(f"Average: {stats['mean_ms']:.2f}ms")
            >>> print(f"P95: {stats['p95_ms']:.2f}ms")
        """
        if endpoint:
            # Stats for specific endpoint
            if endpoint not in self.metrics:
                return {"error": f"No metrics for endpoint: {endpoint}"}

            return self._calculate_stats(endpoint, self.metrics[endpoint])

        # Stats for all endpoints
        all_stats = {}
        for ep, metrics in self.metrics.items():
            all_stats[ep] = self._calculate_stats(ep, metrics)

        all_stats["_summary"] = {
            "total_requests": self.total_requests,
            "tracked_endpoints": len(self.metrics)
        }

        return all_stats

    def _calculate_stats(self, endpoint: str, metrics: deque) -> Dict[str, Any]:
        """Calculate statistics for a metric series."""
        if not metrics:
            return {"count": 0}

        durations = [m.duration_ms for m in metrics]
        cache_hits = sum(1 for m in metrics if m.cache_hit)
        errors = sum(1 for m in metrics if m.status == "error")

        stats = {
            "endpoint": endpoint,
            "count": len(metrics),
            "mean_ms": round(statistics.mean(durations), 2),
            "median_ms": round(statistics.median(durations), 2),
            "min_ms": round(min(durations), 2),
            "max_ms": round(max(durations), 2),
        }

        # Percentiles
        if len(durations) >= 20:  # Need enough samples for percentiles
            sorted_durations = sorted(durations)
            stats["p95_ms"] = round(sorted_durations[int(len(durations) * 0.95)], 2)
            stats["p99_ms"] = round(sorted_durations[int(len(durations) * 0.99)], 2)
        else:
            stats["p95_ms"] = stats["max_ms"]
            stats["p99_ms"] = stats["max_ms"]

        # Rates
        stats["cache_hit_rate"] = round((cache_hits / len(metrics)) * 100, 2)
        stats["error_rate"] = round((errors / len(metrics)) * 100, 2)

        # Recent performance (last 100 requests)
        recent = list(metrics)[-100:]
        if recent:
            recent_durations = [m.duration_ms for m in recent]
            stats["recent_mean_ms"] = round(statistics.mean(recent_durations), 2)

        return stats

    def get_slow_requests(
        self,
        endpoint: Optional[str] = None,
        threshold_ms: float = 1000.0,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get slowest requests above threshold.

        Args:
            endpoint: Filter by endpoint (None = all)
            threshold_ms: Minimum duration to include
            limit: Maximum results to return

        Returns:
            List of slow requests sorted by duration

        Example:
            >>> slow = monitor.get_slow_requests(threshold_ms=500, limit=5)
            >>> for req in slow:
            >>>     print(f"{req['endpoint']}: {req['duration_ms']}ms")
        """
        slow_requests = []

        endpoints = [endpoint] if endpoint else self.metrics.keys()

        for ep in endpoints:
            if ep not in self.metrics:
                continue

            for metric in self.metrics[ep]:
                if metric.duration_ms >= threshold_ms:
                    slow_requests.append({
                        "endpoint": metric.endpoint,
                        "duration_ms": round(metric.duration_ms, 2),
                        "timestamp": metric.timestamp,
                        "status": metric.status,
                        "cache_hit": metric.cache_hit
                    })

        # Sort by duration descending
        slow_requests.sort(key=lambda x: x["duration_ms"], reverse=True)

        return slow_requests[:limit]

    def clear(self, endpoint: Optional[str] = None):
        """
        Clear metrics.

        Args:
            endpoint: Specific endpoint to clear (None = all)
        """
        if endpoint:
            if endpoint in self.metrics:
                self.metrics[endpoint].clear()
        else:
            self.metrics.clear()
            self.total_requests = 0

        logger.info(f"Cleared performance metrics for {endpoint or 'all endpoints'}")

    def export_json(self) -> Dict[str, Any]:
        """
        Export all metrics as JSON.

        Returns:
            Dictionary with all metrics and statistics
        """
        return {
            "stats": self.get_stats(),
            "total_requests": self.total_requests,
            "timestamp": time.time()
        }


# Global monitor instance
_performance_monitor: Optional[PerformanceMonitor] = None


def get_performance_monitor() -> PerformanceMonitor:
    """
    Get singleton PerformanceMonitor instance.

    Returns:
        Shared PerformanceMonitor
    """
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor(window_size=1000)
        logger.info("Initialized performance monitor (1000 samples per endpoint)")
    return _performance_monitor


# Convenience decorators using global monitor
def track_performance(endpoint: str, cache_aware: bool = False):
    """
    Decorator for tracking performance using global monitor.

    Args:
        endpoint: Operation name
        cache_aware: Whether to detect cache hits

    Example:
        >>> from server.utils.performance import track_performance
        >>>
        >>> @track_performance("entity_detection")
        >>> def detect_entities(text):
        >>>     # ... implementation ...
    """
    monitor = get_performance_monitor()
    return monitor.track(endpoint, cache_aware)
