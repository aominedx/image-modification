
import time
import math
import functools


def measure(func, n_runs=10, *args, **kwargs):
    times = list()
    for _ in range(n_runs):
        start = time.perf_counter()
        func(*args, **kwargs)
        times.append(time.perf_counter() - start)

    print(times)

    mean = sum(times) / n_runs
    if n_runs > 1:
        std = math.sqrt(sum((t - mean) ** 2 for t in times) / (n_runs - 1))
        ci = 1.96 * std / math.sqrt(n_runs)   # 95% CI
    else:
        std = ci = 0.0

    for a,i in enumerate(times):
        if i > (mean + ci) or i < (mean - ci):
            times.pop(a)
    print(times)
    print(f"{func.__name__}: {mean:.4f} ± {ci:.4f} с (n={n_runs})")
    return mean, ci


def time_work(n_runs=10):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return measure(func, n_runs, *args, **kwargs)
        return wrapper
    return decorator


