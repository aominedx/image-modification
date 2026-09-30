"""Метрики качества обработки изображений и замер времени.

Не использует сторонних библиотек обработки — только NumPy и стандартный time.
"""
import time
import numpy as np

from core.color_models import rgb_to_yuv_manual


# ============================================================
# Метрики
# ============================================================

def mse(a, b):
    """Mean Squared Error между двумя массивами одинаковой формы."""
    a = a.astype(np.float32)
    b = b.astype(np.float32)
    return float(np.mean((a - b) ** 2))


def psnr(a, b, max_val=255.0):
    """Peak Signal-to-Noise Ratio в децибелах. Если MSE = 0 → возвращаем inf."""
    m = mse(a, b)
    if m == 0.0:
        return float("inf")
    return float(10.0 * np.log10((max_val ** 2) / m))


def delta(a, b):
    """Mean Absolute Difference (среднее абсолютное отклонение)."""
    a = a.astype(np.float32)
    b = b.astype(np.float32)
    return float(np.mean(np.abs(a - b)))


def compute_metrics(reference, target, use_yuv=True):
    """Считает три метрики между эталоном и целевым изображением.

    reference, target — np.ndarray (H, W, 3) uint8 (RGB).
    use_yuv=True — метрики считаются по каналу Y модели YUV.
    use_yuv=False — метрики считаются по всем трём каналам RGB.

    Возвращает dict: {"MSE": ..., "PSNR": ..., "Delta": ...}.
    """
    if reference.shape != target.shape:
        raise ValueError("Изображения должны быть одного размера")

    if use_yuv:
        Y_ref, _, _ = rgb_to_yuv_manual(reference)
        Y_tgt, _, _ = rgb_to_yuv_manual(target)
        return {
            "MSE": mse(Y_ref, Y_tgt),
            "PSNR": psnr(Y_ref, Y_tgt),
            "Delta": delta(Y_ref, Y_tgt),
        }
    else:
        return {
            "MSE": mse(reference, target),
            "PSNR": psnr(reference, target),
            "Delta": delta(reference, target),
        }

def _get_filter_list():
    """Список доступных фильтров: [(имя, функция), ...].

    Каждая функция принимает app и применяет фильтр к app.base_image,
    записывая результат в app.processed_image.
    """
    from core.filters import (
        apply_average_filter,
        apply_fast_median_filter,
        apply_recursive_average_filter,
        apply_unsharp_mask,
    )

    def _avg(app):
        apply_average_filter(app, n_jobs=4)

    def _median(app):
        apply_fast_median_filter(app, n_jobs=4)

    def _rec(app):
        apply_recursive_average_filter(app, n_jobs=4)

    def _usm(app):
        apply_unsharp_mask(app, n_jobs=4)

    return [
        ("Усредняющий", _avg),
        ("Медианный (гистограммный)", _median),
        ("Рекурсивный усредняющий", _rec),
        ("UnsharpMask", _usm),
    ]
# ============================================================
# Замер времени
# ============================================================

def measure_time(func, *args, n_runs=5, warmup=1, **kwargs):
    """Замеряет время работы функции в миллисекундах.

    Возвращает (mean_ms, ci_ms) — среднее и 95% доверительный интервал.
    Первые warmup прогонов не учитываются (прогрев кэша).
    """
    for _ in range(warmup):
        func(*args, **kwargs)

    times = []
    for _ in range(n_runs):
        t0 = time.perf_counter()
        func(*args, **kwargs)
        times.append((time.perf_counter() - t0) * 1000.0)   # в миллисекундах

    times = np.array(times, dtype=np.float64)
    mean = float(times.mean())
    if n_runs > 1:
        std = float(times.std(ddof=1))
        ci = 1.96 * std / np.sqrt(n_runs)
    else:
        ci = 0.0
    return mean, ci


# ============================================================
# Сравнение нескольких фильтров
# ============================================================

def compare_filters(app):
    """Сравнивает фильтры по метрикам и времени.

    Читает reference из app.original_image, noisy из app.processed_image,
    параметры — из app.metrics_space_var и app.metrics_runs_var.
    Результат сохраняет в app.metrics_results и показывает в отдельном окне.
    """
    from tkinter import messagebox

    if app.original_image is None:
        messagebox.showerror("Ошибка", "Нет изображения")
        return
    if app.processed_image is None:
        messagebox.showerror(
            "Ошибка",
            "Сначала наложите шум — processed_image будет использоваться как зашумлённое",
        )
        return

    reference = np.array(app.original_image.convert("RGB"))
    noisy = np.array(app.processed_image.convert("RGB"))

    use_yuv = app.metrics_space_var.get() == "YUV (Y)"
    n_runs = int(app.metrics_runs_var.get())

    filters = _get_filter_list()

    results = _run_comparison(app, filters, reference, noisy, n_runs, use_yuv)

    app.metrics_results = results

    # показать отчёт
    from ui.metrics_widgets import show_metrics_report
    show_metrics_report(app.root, results)


def _run_comparison(app, filters, reference, noisy, n_runs, use_yuv):
    """Внутренняя функция: прогоняет фильтры, считает метрики и время."""
    results = []

    # базовый уровень — зашумлённое изображение без обработки
    base = compute_metrics(reference, noisy, use_yuv=use_yuv)
    results.append({
        "name": "Зашумлённое (без обработки)",
        "MSE": base["MSE"],
        "PSNR": base["PSNR"],
        "Delta": base["Delta"],
        "time_ms": 0.0,
        "time_ci": 0.0,
    })

    for name, apply_func in filters:
        # --- метрики ---
        app.processed_image = None
        app.base_image = _to_pil(noisy)
        apply_func(app)
        filtered = np.array(app.processed_image.convert("RGB"))
        m = compute_metrics(reference, filtered, use_yuv=use_yuv)

        # --- время ---
        app.base_image = _to_pil(noisy)
        mean_ms, ci_ms = measure_time(apply_func, app, n_runs=n_runs, warmup=1)

        results.append({
            "name": name,
            "MSE": m["MSE"],
            "PSNR": m["PSNR"],
            "Delta": m["Delta"],
            "time_ms": mean_ms,
            "time_ci": ci_ms,
        })

    return results


def _to_pil(rgb_array):
    """np.ndarray (H,W,3) uint8 → PIL.Image."""
    from PIL import Image
    return Image.fromarray(rgb_array)