"""Построение графиков сравнения фильтров по метрикам и быстродействию.

Использует matplotlib. Сохраняет все графики в папку ./reports/.
"""
import os
import numpy as np
import matplotlib.pyplot as plt


REPORTS_DIR = "reports"


def _ensure_reports_dir():
    os.makedirs(REPORTS_DIR, exist_ok=True)


# ============================================================
# График 1. Метрики качества — MSE и PSNR (две оси)
# ============================================================

def plot_metrics(results, title="Метрики качества фильтров", filename="metrics.png"):
    """Столбчатая диаграмма: MSE и PSNR для каждого фильтра.

    results — список dict-ов, как возвращает core.metrics.compare_filters.
              Каждый элемент: {"name", "MSE", "PSNR", "Delta", ...}
    """
    _ensure_reports_dir()

    names = [r["name"] for r in results]
    mse = [r["MSE"] for r in results]
    psnr = [r["PSNR"] for r in results]

    x = np.arange(len(names))
    width = 0.4

    fig, ax1 = plt.subplots(figsize=(10, 5))

    # левая ось — MSE
    bars1 = ax1.bar(x - width/2, mse, width, label="MSE", color="steelblue")
    ax1.set_ylabel("MSE (меньше — лучше)", color="steelblue")
    ax1.tick_params(axis="y", labelcolor="steelblue")
    ax1.set_xticks(x)
    ax1.set_xticklabels(names, rotation=15, ha="right")

    # правая ось — PSNR
    ax2 = ax1.twinx()
    psnr_plot = [p if p != float("inf") else 100.0 for p in psnr]
    bars2 = ax2.bar(x + width/2, psnr_plot, width, label="PSNR", color="darkorange")
    ax2.set_ylabel("PSNR, дБ (больше — лучше)", color="darkorange")
    ax2.tick_params(axis="y", labelcolor="darkorange")

    # подписи значений над столбцами
    for bar, val in zip(bars1, mse):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                 f"{val:.0f}", ha="center", va="bottom", fontsize=8)
    for bar, val in zip(bars2, psnr):
        label = "∞" if val == float("inf") else f"{val:.1f}"
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                 label, ha="center", va="bottom", fontsize=8)

    plt.title(title)
    plt.tight_layout()
    path = os.path.join(REPORTS_DIR, filename)
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"Сохранено: {path}")


# ============================================================
# График 2. Время работы — столбцы с усами ошибок
# ============================================================

def plot_time(results, title="Быстродействие фильтров", filename="time.png"):
    """Столбчатая диаграмма времени с 95% доверительными интервалами."""
    _ensure_reports_dir()

    names = [r["name"] for r in results]
    times = [r["time_ms"] for r in results]
    cis = [r.get("time_ci", 0.0) for r in results]

    x = np.arange(len(names))

    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.bar(x, times, yerr=cis, capsize=5,
                  color="seagreen", edgecolor="black")

    ax.set_ylabel("Время, мс (меньше — лучше)")
    ax.set_xticks(x)
    ax.set_xticklabels(names, rotation=15, ha="right")
    ax.set_title(title)
    ax.grid(axis="y", linestyle="--", alpha=0.4)

    for bar, val in zip(bars, times):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                f"{val:.1f}", ha="center", va="bottom", fontsize=9)

    plt.tight_layout()
    path = os.path.join(REPORTS_DIR, filename)
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"Сохранено: {path}")


# ============================================================
# График 3. Delta (среднее абсолютное отклонение)
# ============================================================

def plot_delta(results, title="Среднее абсолютное отклонение (Delta)",
               filename="delta.png"):
    """Отдельный график Delta — для наглядности."""
    _ensure_reports_dir()

    names = [r["name"] for r in results]
    delta = [r["Delta"] for r in results]

    x = np.arange(len(names))

    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.bar(x, delta, color="indianred", edgecolor="black")
    ax.set_ylabel("Delta (меньше — лучше)")
    ax.set_xticks(x)
    ax.set_xticklabels(names, rotation=15, ha="right")
    ax.set_title(title)
    ax.grid(axis="y", linestyle="--", alpha=0.4)

    for bar, val in zip(bars, delta):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                f"{val:.2f}", ha="center", va="bottom", fontsize=9)

    plt.tight_layout()
    path = os.path.join(REPORTS_DIR, filename)
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"Сохранено: {path}")


# ============================================================
# График 4. Зависимость времени от числа потоков
# ============================================================

def plot_speedup(data, title="Зависимость времени от числа потоков",
                 filename="speedup.png"):
    """Кривые времени для каждого фильтра в зависимости от n_jobs.

    data — dict: {имя_фильтра: [(n_jobs, time_ms), ...], ...}
    """
    _ensure_reports_dir()

    plt.figure(figsize=(10, 5))
    for name, points in data.items():
        ns = [p[0] for p in points]
        ts = [p[1] for p in points]
        plt.plot(ns, ts, marker="o", label=name)

    plt.xlabel("Число потоков")
    plt.ylabel("Время, мс")
    plt.title(title)
    plt.xticks([1, 2, 3, 4])
    plt.grid(True, linestyle="--", alpha=0.4)
    plt.legend()
    plt.tight_layout()
    path = os.path.join(REPORTS_DIR, filename)
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"Сохранено: {path}")


# ============================================================
# График 5. Ускорение быстрых алгоритмов относительно классических
# ============================================================

def plot_algorithm_speedup(title="Ускорение быстрых алгоритмов",
                           filename="algorithm_speedup.png"):
    """Сравнение ускорения быстрых и классических реализаций.

    Данные берутся из таблиц 10 и 11 отчёта. Можно заменить на свои.
    """
    _ensure_reports_dir()

    mp = [0.92, 2.07, 3.69, 8.29]
    speedup_avg = [18.3, 24.2, 22.1, 21.2]   # усредняющий: классический / быстрый
    speedup_med = [38.3, 47.8, 47.2, 45.5]   # медианный: классический / быстрый

    plt.figure(figsize=(9, 5))
    plt.plot(mp, speedup_avg, marker="o", label="Усредняющий (NumPy vs Python-цикл)")
    plt.plot(mp, speedup_med, marker="s", label="Медианный (гистограммный vs сортировка)")

    plt.xlabel("Размер изображения, Мп")
    plt.ylabel("Ускорение, раз")
    plt.title(title)
    plt.grid(True, linestyle="--", alpha=0.4)
    plt.legend()
    plt.tight_layout()
    path = os.path.join(REPORTS_DIR, filename)
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"Сохранено: {path}")


# ============================================================
# График 6. Сравнение метрик при разных типах шума (группированные столбцы)
# ============================================================

def plot_noise_comparison(title="Сравнение фильтров при разных типах шума",
                          filename="noise_comparison.png"):
    """Три группы столбцов (импульсный, аддитивный, мультипликативный).

    В каждой группе — по фильтру. Ось Y — MSE (или любая другая метрика).
    Данные можно заменить на свои.
    """
    _ensure_reports_dir()

    filters = ["Зашумлённое", "Усредняющий", "Медианный", "Рекурсивный", "UnsharpMask"]
    impulse     = [3124.5, 856.3, 118.7, 2104.2, 3489.6]
    additive    = [843.2, 298.5, 412.6, 356.1, 1105.4]
    multiplicative = [1245.8, 512.3, 645.1, 720.4, 1580.2]

    x = np.arange(len(filters))
    width = 0.25

    fig, ax = plt.subplots(figsize=(11, 5))
    ax.bar(x - width, impulse, width, label="Импульсный", color="steelblue")
    ax.bar(x,         additive, width, label="Аддитивный", color="darkorange")
    ax.bar(x + width, multiplicative, width, label="Мультипликативный", color="seagreen")

    ax.set_ylabel("MSE (меньше — лучше)")
    ax.set_xticks(x)
    ax.set_xticklabels(filters, rotation=15, ha="right")
    ax.set_title(title)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    ax.legend()

    plt.tight_layout()
    path = os.path.join(REPORTS_DIR, filename)
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"Сохранено: {path}")


# ============================================================
# Все графики сразу
# ============================================================

def plot_all(results):
    """Строит все графики по результатам compare_filters."""
    plot_metrics(results)
    plot_time(results)
    plot_delta(results)


# ============================================================
# Демонстрация: строит графики на тестовых данных
# ============================================================

if __name__ == "__main__":
    demo = [
        {"name": "Зашумлённое", "MSE": 3124.5, "PSNR": 13.2, "Delta": 42.5,
         "time_ms": 0.0, "time_ci": 0.0},
        {"name": "Усредняющий",  "MSE": 856.3,  "PSNR": 18.8, "Delta": 22.4,
         "time_ms": 45.3, "time_ci": 2.1},
        {"name": "Медианный",    "MSE": 118.7,  "PSNR": 27.4, "Delta": 6.3,
         "time_ms": 121.5, "time_ci": 5.3},
        {"name": "Рекурсивный",  "MSE": 2104.2, "PSNR": 14.9, "Delta": 35.1,
         "time_ms": 32.7, "time_ci": 1.8},
        {"name": "UnsharpMask",  "MSE": 3489.6, "PSNR": 12.7, "Delta": 45.8,
         "time_ms": 61.4, "time_ci": 3.2},
    ]

    plot_all(demo)

    speedup_data = {
        "Усредняющий": [(1, 61), (2, 39), (3, 31), (4, 26)],
        "Медианный":   [(1, 187), (2, 121), (3, 96), (4, 80)],
        "Рекурсивный": [(1, 42), (2, 28), (3, 23), (4, 19)],
        "UnsharpMask": [(1, 92), (2, 60), (3, 48), (4, 41)],
    }
    plot_speedup(speedup_data)

    plot_algorithm_speedup()
    plot_noise_comparison()