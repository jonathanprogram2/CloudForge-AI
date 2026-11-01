
from scripts.benchmark_performance import percentile


def test_p50_latency():
    values = [100, 200, 300, 400, 500]
    assert percentile(values, 50) == 300


def test_p95_latency():
    values = [100, 200, 300, 400, 500]
    assert percentile(values, 95) == 480


def test_single_measurement():
    assert percentile([250], 95) == 250


def test_empty_measurements():
    assert percentile([], 95) is None
