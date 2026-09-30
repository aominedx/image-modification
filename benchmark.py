"""Бенчмарк алгоритмов обработки изображений с перебором n_jobs."""
import sys
import time
import math
from PIL import Image

from core.contrast import adjust_contrast_brightness
from core.histograms import bcet_correction, gamma_correction


# ---------- статистика ----------

def measure(func, n_runs=10, *args, **kwargs):
    """Запускает func n_runs раз, возвращает (mean, ci)."""
    times = []
    for _ in range(n_runs):
        start = time.perf_counter()
        func(*args, **kwargs)
        times.append(time.perf_counter() - start)

    mean = sum(times) / n_runs
    if n_runs > 1:
        std = math.sqrt(sum((t - mean) ** 2 for t in times) / (n_runs - 1))
        ci = 1.96 * std / math.sqrt(n_runs)
    else:
        ci = 0.0
    return mean, ci


# ---------- заглушка вместо приложения ----------

class DummyVar:
    """Имитация tk.DoubleVar — просто возвращает фиксированное значение."""
    def __init__(self, value):
        self._value = value
    def get(self):
        return self._value


class DummyApp:
    """Минимальная заглушка ImageProcessor для бенчмарка."""
    def __init__(self, image_path):
        self.original_image = Image.open(image_path).convert("RGB")
        self.base_image = self.original_image.copy()
        self.processed_image = None
        self.contrast_var = DummyVar(1.5)
        self.brightness_var = DummyVar(1.2)

    def display_images(self):
        pass  # GUI не нужен


# ---------- бенчмарк ----------

def run_benchmark(image_path, n_runs=10):
    app = DummyApp(image_path)
    print(f"Изображение: {image_path}")
    print(f"Размер: {app.original_image.size}")
    print(f"Прогонов на точку: {n_runs}")
    print()

    tests = [
        ("Контраст/яркость", adjust_contrast_brightness, {}),
        ("BCET",             bcet_correction,            {}),
        ("Гамма",            gamma_correction,           {"gamma": 1.5}),
    ]

    results = {}

    for name, func, extra_kwargs in tests:
        print(f"--- {name} ---")
        rows = []
        for n_jobs in (1, 2, 3, 4):
            mean, ci = measure(func, n_runs, app, n_jobs=n_jobs, **extra_kwargs)
            rows.append((n_jobs, mean, ci))
            print(f"  n_jobs={n_jobs}: {mean:.4f} ± {ci:.4f} с")
        results[name] = rows
        print()

    return results


def print_table(results):
    """Печатает итоговую таблицу + ускорение относительно n_jobs=1."""
    print("=" * 72)
    print(f"{'Алгоритм':<20}{'n_jobs':>8}{'среднее, с':>14}{'95% CI, с':>12}{'ускорение':>14}")
    print("-" * 72)
    for name, rows in results.items():
        t1 = rows[0][1]  # время при n_jobs=1
        for n_jobs, mean, ci in rows:
            speedup = t1 / mean if mean > 0 else 0.0
            print(f"{name:<20}{n_jobs:>8}{mean:>14.4f}{ci:>12.4f}{speedup:>13.2f}x")
        print("-" * 72)
    print("=" * 72)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python benchmark.py <путь_к_изображению>")
        sys.exit(1)

    image_path = sys.argv[1]
    results = run_benchmark(image_path, n_runs=10)
    print_table(results)