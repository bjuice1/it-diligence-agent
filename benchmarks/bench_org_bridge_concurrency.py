"""
P3 FIX #11: Performance Benchmark for Organization Bridge Lock Contention

Measures throughput and latency of build_organization_from_facts() under
concurrent load to quantify the performance impact of threading.RLock.

Usage:
    python benchmarks/bench_org_bridge_concurrency.py

Output:
    - Calls/sec for 1, 5, 10, 20 threads
    - Average latency, p50, p95, p99
    - Lock contention overhead vs single-threaded baseline
"""

import time
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import sys

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from stores.fact_store import FactStore
from services.organization_bridge import build_organization_from_facts


def setup_fact_store(fact_count: int = 50) -> FactStore:
    """Create a FactStore with test data for benchmarking."""
    fact_store = FactStore(deal_id="benchmark-test")

    # Add a mix of leadership and role facts
    for i in range(fact_count):
        category = "leadership" if i < 5 else "roles"
        fact_store.add_fact(
            domain="organization",
            category=category,
            item=f"Role {i}",
            details={'reports_to': f'Manager {i // 5}' if i >= 5 else None},
            status="documented",
            evidence={'exact_quote': f'Role {i} description'},
            entity="target"
        )

    return fact_store


def benchmark_single_call(fact_store: FactStore) -> float:
    """Benchmark a single call and return duration in seconds."""
    start = time.perf_counter()
    store, status = build_organization_from_facts(
        fact_store,
        entity="target",
        enable_assumptions=True,
        deal_id="benchmark-test"
    )
    duration = time.perf_counter() - start
    return duration


def benchmark_concurrent_calls(
    fact_store: FactStore,
    num_threads: int,
    calls_per_thread: int = 10
) -> dict:
    """
    Benchmark concurrent calls with specified thread count.

    Returns:
        dict with metrics: total_calls, duration, calls_per_sec, latencies
    """
    latencies = []

    def worker_task(task_id: int):
        """Each worker makes multiple calls and records latencies."""
        task_latencies = []
        for _ in range(calls_per_thread):
            lat = benchmark_single_call(fact_store)
            task_latencies.append(lat)
        return task_latencies

    # Execute benchmark
    start = time.perf_counter()

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(worker_task, i) for i in range(num_threads)]

        for future in as_completed(futures):
            task_latencies = future.result()
            latencies.extend(task_latencies)

    total_duration = time.perf_counter() - start

    # Calculate metrics
    total_calls = num_threads * calls_per_thread
    calls_per_sec = total_calls / total_duration

    sorted_latencies = sorted(latencies)
    p50 = sorted_latencies[len(sorted_latencies) // 2]
    p95 = sorted_latencies[int(len(sorted_latencies) * 0.95)]
    p99 = sorted_latencies[int(len(sorted_latencies) * 0.99)]

    return {
        "num_threads": num_threads,
        "total_calls": total_calls,
        "total_duration": total_duration,
        "calls_per_sec": calls_per_sec,
        "latencies": latencies,
        "avg_latency": statistics.mean(latencies),
        "median_latency": p50,
        "p95_latency": p95,
        "p99_latency": p99,
        "min_latency": min(latencies),
        "max_latency": max(latencies),
    }


def print_separator():
    """Print separator line."""
    print("=" * 80)


def print_metrics(metrics: dict):
    """Print benchmark metrics in formatted table."""
    print(f"Threads:        {metrics['num_threads']:>6}")
    print(f"Total Calls:    {metrics['total_calls']:>6}")
    print(f"Duration:       {metrics['total_duration']:>6.2f}s")
    print(f"Throughput:     {metrics['calls_per_sec']:>6.1f} calls/sec")
    print()
    print(f"Latency (ms):")
    print(f"  Min:          {metrics['min_latency'] * 1000:>6.2f}")
    print(f"  Avg:          {metrics['avg_latency'] * 1000:>6.2f}")
    print(f"  Median (p50): {metrics['median_latency'] * 1000:>6.2f}")
    print(f"  p95:          {metrics['p95_latency'] * 1000:>6.2f}")
    print(f"  p99:          {metrics['p99_latency'] * 1000:>6.2f}")
    print(f"  Max:          {metrics['max_latency'] * 1000:>6.2f}")


def main():
    """Run benchmark suite."""
    print_separator()
    print("Organization Bridge Concurrency Benchmark")
    print_separator()
    print()

    # Setup
    print("Setting up FactStore with 50 organization facts...")
    fact_store = setup_fact_store(fact_count=50)
    print("✓ Setup complete")
    print()

    # Warmup
    print("Warming up (5 calls)...")
    for _ in range(5):
        benchmark_single_call(fact_store)
    print("✓ Warmup complete")
    print()

    # Benchmark different thread counts
    thread_counts = [1, 5, 10, 20]
    results = []

    for num_threads in thread_counts:
        print_separator()
        print(f"Benchmarking with {num_threads} thread(s)...")
        print_separator()

        metrics = benchmark_concurrent_calls(
            fact_store,
            num_threads=num_threads,
            calls_per_thread=10
        )
        results.append(metrics)

        print_metrics(metrics)
        print()

    # Summary comparison
    print_separator()
    print("SUMMARY: Lock Contention Analysis")
    print_separator()
    print()

    baseline = results[0]  # Single-threaded baseline

    print(f"{'Threads':<10} {'Calls/Sec':<15} {'Speedup':<15} {'Avg Latency (ms)':<20} {'Overhead'}")
    print("-" * 80)

    for r in results:
        speedup = r['calls_per_sec'] / baseline['calls_per_sec']
        overhead_pct = ((r['avg_latency'] / baseline['avg_latency']) - 1) * 100

        print(
            f"{r['num_threads']:<10} "
            f"{r['calls_per_sec']:<15.1f} "
            f"{speedup:<15.2f}x "
            f"{r['avg_latency'] * 1000:<20.2f} "
            f"{overhead_pct:+.1f}%"
        )

    print()

    # Analysis
    print_separator()
    print("ANALYSIS")
    print_separator()
    print()

    max_threads = results[-1]
    scalability = max_threads['calls_per_sec'] / baseline['calls_per_sec']

    if scalability > 15:
        verdict = "✅ EXCELLENT - Minimal lock contention"
    elif scalability > 10:
        verdict = "✅ GOOD - Acceptable lock contention"
    elif scalability > 5:
        verdict = "⚠️  MODERATE - Some lock contention overhead"
    else:
        verdict = "❌ HIGH - Significant lock contention limiting scalability"

    print(f"Scalability (20 threads vs 1 thread): {scalability:.2f}x")
    print(f"Verdict: {verdict}")
    print()

    if scalability < 10:
        print("RECOMMENDATIONS:")
        print("- Consider using per-request FactStore instances instead of shared")
        print("- Lock is coarse-grained (entire FactStore modification)")
        print("- For high-concurrency deployments, use connection pooling with separate stores")
    else:
        print("RECOMMENDATIONS:")
        print("- Current lock implementation is performant for expected load")
        print("- Safe to use shared FactStore in multi-threaded Flask deployment")
        print("- Monitor lock contention in production with profiling if needed")

    print()
    print_separator()


if __name__ == "__main__":
    main()
