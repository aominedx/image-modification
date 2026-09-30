"""Линейная фильтрация: усредняющий фильтр и UnsharpMask.

Параллельная обработка через multiprocessing.Pool: изображение делится
на горизонтальные полосы, каждая полоса обрабатывается в отдельном процессе.
"""
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view
from PIL import Image
from tkinter import messagebox
from multiprocessing import Pool

from core.color_models import rgb_to_yuv_manual, yuv_to_rgb_manual


# ============================================================
# Построение ядер
# ============================================================

def _build_average_kernel(size, shape="square", orientation="row"):
    """Строит ядро усредняющего фильтра.

    size        — размер маски (нечётное число).
    shape       — "square" (квадрат), "rect" (прямоугольник), "1d" (одномерный).
    orientation — для "1d": "row" (по строке) или "col" (по столбцу).

    Возвращает np.ndarray формы (kh, kw), нормированный так, что сумма = 1.
    """
    if size % 2 == 0:
        size += 1  # маска должна быть нечётной

    if shape == "square":
        kernel = np.ones((size, size), dtype=np.float32)
    elif shape == "rect":
        # прямоугольник: высота = size, ширина = 2*size+1 (пример)
        kh = size
        kw = 2 * size + 1
        kernel = np.ones((kh, kw), dtype=np.float32)
    elif shape == "1d":
        if orientation == "row":
            kernel = np.ones((1, size), dtype=np.float32)
        else:  # "col"
            kernel = np.ones((size, 1), dtype=np.float32)
    else:
        kernel = np.ones((size, size), dtype=np.float32)

    kernel /= kernel.sum()
    return kernel


def _build_custom_kernel(kernel_values, kh, kw):
    """Строит ядро из введённых пользователем коэффициентов.

    kernel_values — список чисел длиной kh*kw (по строкам, сверху вниз).
    Возвращает np.ndarray формы (kh, kw). Нормировка не делается —
    пользователь сам задаёт коэффициенты.
    """
    arr = np.array(kernel_values, dtype=np.float32)
    if arr.size != kh * kw:
        raise ValueError(f"Ожидалось {kh*kw} коэффициентов, получено {arr.size}")
    return arr.reshape((kh, kw))


# ============================================================
# Свёртка (одна полоса изображения)
# ============================================================

def _convolve_channel_strip(args):
    """Свёртка одноканальной полосы с ядром через sliding_window_view."""
    strip, kernel = args
    kh, kw = kernel.shape
    ph, pw = kh // 2, kw // 2

    # дополняем края повторением
    padded = np.pad(strip, ((ph, ph), (pw, pw)), mode="edge")

    # "вид" на все окна размера (kh, kw): форма (h, w, kh, kw)
    windows = sliding_window_view(padded, (kh, kw))

    # сумма произведений по последним двум осям — одна C-операция
    return np.einsum("ijkl,kl->ij", windows, kernel).astype(np.float32)


def _convolve_rgb_strip(args):
    """Свёртка RGB-полосы: каждое ядро применяется к соответствующему каналу.

    args = (strip_rgb, kernels)
    strip_rgb — np.ndarray формы (h_strip, w, 3), uint8.
    kernels   — список из трёх ядер (или одного, которое применится ко всем).
    """
    strip_rgb, kernels = args
    h, w, _ = strip_rgb.shape
    out = np.zeros((h, w, 3), dtype=np.float32)

    for c in range(3):
        kernel = kernels[c] if isinstance(kernels, (list, tuple)) else kernels
        out[:, :, c] = _convolve_channel_strip((strip_rgb[:, :, c].astype(np.float32), kernel))

    return out


# ============================================================
# Разбиение на полосы и параллельная обработка
# ============================================================

def _split_into_strips(array, n_jobs):
    """Делит 2D- или 3D-массив на n_jobs горизонтальных полос."""
    return np.array_split(array, n_jobs, axis=0)


def _parallel_convolve_channel(channel, kernel, n_jobs):
    """Параллельная свёртка одноканального изображения."""
    strips = _split_into_strips(channel, n_jobs)
    args = [(strip.astype(np.float32), kernel) for strip in strips]
    with Pool(n_jobs) as pool:
        results = pool.map(_convolve_channel_strip, args)
    return np.concatenate(results, axis=0)


def _parallel_convolve_rgb(rgb_array, kernels, n_jobs):
    """Параллельная свёртка RGB-изображения."""
    strips = _split_into_strips(rgb_array, n_jobs)
    args = [(strip, kernels) for strip in strips]
    with Pool(n_jobs) as pool:
        results = pool.map(_convolve_rgb_strip, args)
    return np.concatenate(results, axis=0)


# ============================================================
# Усредняющий фильтр
# ============================================================


def apply_average_filter(app, n_jobs=4,
                         color_space="RGB",
                         channel_name="Y",
                         kernel_size=3,
                         kernel_shape="square",
                         orientation="row",
                         custom_kernel_values=None,
                         kh=3, kw=3):
    """Усредняющий линейный фильтр.

    Параметры:
      color_space          — "RGB" или "YUV".
      channel_name         — к какому каналу применить (для RGB: R/G/B/ALL,
                             для YUV: Y/U/V/ALL).
      kernel_size          — размер маски (для стандартного ядра).
      kernel_shape         — "square" | "rect" | "1d".
      orientation          — "row" | "col" (только для "1d").
      custom_kernel_values — если задан список коэффициентов, используется
                             пользовательское ядро размера kh × kw.
      kh, kw               — размеры пользовательского ядра.
    """
    if not app.original_image:
        messagebox.showerror("Ошибка", "Нет изображения")
        return

        # --- читаем параметры из UI ---
    color_space = app.avg_color_var.get()
    channel_name = app.avg_channel_var.get()
    kernel_size = app.avg_size_var.get()
    kernel_shape = app.avg_shape_var.get()
    orientation = app.avg_orient_var.get()

    # --- разбор пользовательского ядра ---
    custom = None
    text = app.avg_custom_var.get().strip()
    if text:
        try:
            custom = [float(x) for x in text.split(",")]
        except ValueError:
            messagebox.showerror("Ошибка", "Коэффициенты должны быть числами через запятую")
            return
        kh = kw = kernel_size
    else:
        kh = kw = kernel_size

    # --- выбор ядра ---
    if custom is not None:
        try:
            kernel = _build_custom_kernel(custom, kh, kw)
        except ValueError as e:
            messagebox.showerror("Ошибка", str(e))
            return
    else:
        kernel = _build_average_kernel(kernel_size, kernel_shape, orientation)

    rgb_array = np.array(app.original_image.convert("RGB"))

    # --- выбираем ядро ---
    if custom_kernel_values is not None:
        try:
            kernel = _build_custom_kernel(custom_kernel_values, kh, kw)
        except ValueError as e:
            messagebox.showerror("Ошибка", str(e))
            return
    else:
        kernel = _build_average_kernel(kernel_size, kernel_shape, orientation)

    # --- обрабатываем в зависимости от модели ---
    if color_space == "RGB":
        if channel_name == "ALL":
            out = _parallel_convolve_rgb(rgb_array, kernel, n_jobs)
            out = np.clip(out, 0, 255).astype(np.uint8)
        else:
            idx = {"R": 0, "G": 1, "B": 2}.get(channel_name)
            if idx is None:
                messagebox.showerror("Ошибка", f"Неизвестный канал: {channel_name}")
                return
            channel = rgb_array[:, :, idx].astype(np.float32)
            filtered = _parallel_convolve_channel(channel, kernel, n_jobs)
            out = rgb_array.copy()
            out[:, :, idx] = np.clip(filtered, 0, 255).astype(np.uint8)

    elif color_space == "YUV":
        Y, U, V = rgb_to_yuv_manual(rgb_array)
        Y = Y.astype(np.float32)

        if channel_name == "Y":
            Y_new = _parallel_convolve_channel(Y, kernel, n_jobs)
        elif channel_name == "U":
            U_new = _parallel_convolve_channel(U.astype(np.float32), kernel, n_jobs)
            Y_new = Y
            U = U_new
        elif channel_name == "V":
            V_new = _parallel_convolve_channel(V.astype(np.float32), kernel, n_jobs)
            Y_new = Y
            V = V_new
        elif channel_name == "ALL":
            Y = _parallel_convolve_channel(Y, kernel, n_jobs)
            U = _parallel_convolve_channel(U.astype(np.float32), kernel, n_jobs)
            V = _parallel_convolve_channel(V.astype(np.float32), kernel, n_jobs)
            Y_new = Y
        else:
            messagebox.showerror("Ошибка", f"Неизвестный канал: {channel_name}")
            return

        out = yuv_to_rgb_manual(Y_new, np.clip(U, 0, 255), np.clip(V, 0, 255))
    else:
        messagebox.showerror("Ошибка", f"Неизвестная модель: {color_space}")
        return

    app.processed_image = Image.fromarray(out)
    app.display_images()


# ============================================================
# UnsharpMask
# ============================================================

def _unsharp_mask_strip(args):
    """UnsharpMask для одной полосы канала Y.

    args = (strip, blur_kernel, amount, threshold)
    strip       — np.ndarray (h_strip, w) float32.
    blur_kernel — ядро размытия (нормированное).
    amount      — коэффициент усиления разницы (например, 0.5-2.0).
    threshold   — порог: разница меньше порога не усиливается.
    """
    strip, blur_kernel, amount, threshold = args

    # размытие полосы
    blurred = _convolve_channel_strip((strip, blur_kernel))

    # разница между исходным и размытым
    diff = strip - blurred

    # отсекаем слабые перепады по порогу
    mask = np.abs(diff) >= threshold
    diff = np.where(mask, diff, 0.0)

    # усиливаем и прибавляем к исходному
    sharpened = strip + amount * diff
    return np.clip(sharpened, 0, 255).astype(np.float32)


def apply_unsharp_mask(app, n_jobs=4,
                       blur_size=5,
                       blur_shape="square",
                       amount=1.0,
                       threshold=0.0,
                       custom_blur_values=None,
                       kh=5, kw=5):
    """UnsharpMask на канале Y модели YUV.

    Параметры:
      blur_size          — размер маски размытия.
      blur_shape         — "square" | "rect" | "1d".
      amount             — коэффициент усиления (0..3).
      threshold          — порог (0..255).
      custom_blur_values — если задан список коэффициентов, используется
                           пользовательское ядро размытия размера kh × kw.
    """
    if not app.original_image:
        messagebox.showerror("Ошибка", "Нет изображения")
        return

    blur_size = app.usm_blur_var.get()
    blur_shape = app.usm_shape_var.get()
    amount = app.usm_amount_var.get()
    threshold = app.usm_threshold_var.get()

    custom = None
    text = app.usm_custom_var.get().strip()
    if text:
        try:
            custom = [float(x) for x in text.split(",")]
        except ValueError:
            messagebox.showerror("Ошибка", "Коэффициенты должны быть числами через запятую")
            return
        kh = kw = blur_size
    else:
        kh = kw = blur_size

    rgb_array = np.array(app.original_image.convert("RGB"))
    Y, U, V = rgb_to_yuv_manual(rgb_array)
    Y = Y.astype(np.float32)

    # --- ядро размытия ---
    if custom_blur_values is not None:
        try:
            blur_kernel = _build_custom_kernel(custom_blur_values, kh, kw)
            # нормируем, чтобы яркость не «уехала»
            s = blur_kernel.sum()
            if s == 0:
                messagebox.showerror("Ошибка", "Сумма коэффициентов ядра равна 0")
                return
            blur_kernel = blur_kernel / s
        except ValueError as e:
            messagebox.showerror("Ошибка", str(e))
            return
    else:
        blur_kernel = _build_average_kernel(blur_size, blur_shape, "row")

    # --- параллельная обработка полос ---
    strips = _split_into_strips(Y, n_jobs)
    args = [(strip, blur_kernel, amount, threshold) for strip in strips]
    with Pool(n_jobs) as pool:
        results = pool.map(_unsharp_mask_strip, args)

    Y_new = np.concatenate(results, axis=0).astype(np.float32)

    # --- сборка обратно в RGB ---
    rgb_new = yuv_to_rgb_manual(Y_new, U, V)
    app.processed_image = Image.fromarray(rgb_new)
    app.display_images()

# ============================================================
# Рекурсивный среднеарифметический фильтр
# ============================================================

def _recursive_avg_strip(args):
    """Рекурсивный усредняющий фильтр вдоль строк через np.frompyfunc.accumulate."""
    strip, alpha = args
    y = strip.astype(np.float32)

    # рекурсивное правило в виде функции от двух аргументов:
    #   step(acc, x) = (1-alpha) * x + alpha * acc
    def step(acc, x):
        return (1.0 - alpha) * x + alpha * acc

    # np.frompyfunc создаёт "универсальную функцию", accumulate применяет её
    # последовательно вдоль оси, как reduce
    ufunc = np.frompyfunc(step, 2, 1)

    # ВАЖНО: accumulate требует, чтобы первая ось была осью рекурсии,
    # поэтому идём по строкам через axis=1
    out = ufunc.accumulate(y, axis=1)

    return out.astype(np.float32)


def apply_recursive_average_filter(app, n_jobs=4):
    """Рекурсивный среднеарифметический фильтр по каналу Y модели YUV.

    Читает параметры из app.rec_alpha_var.
    """
    if not app.original_image:
        messagebox.showerror("Ошибка", "Нет изображения")
        return

    alpha = float(app.rec_alpha_var.get())
    if not (0.0 <= alpha < 1.0):
        messagebox.showerror("Ошибка", "Коэффициент α должен быть в [0, 1)")
        return

    rgb_array = np.array(app.original_image.convert("RGB"))
    Y, U, V = rgb_to_yuv_manual(rgb_array)
    Y = Y.astype(np.float32)

    strips = _split_into_strips(Y, n_jobs)
    args = [(strip, alpha) for strip in strips]

    with Pool(n_jobs) as pool:
        results = pool.map(_recursive_avg_strip, args)

    Y_new = np.concatenate(results, axis=0).astype(np.float32)
    rgb_new = yuv_to_rgb_manual(Y_new, U, V)

    app.processed_image = Image.fromarray(rgb_new)
    app.display_images()

# ============================================================
# Быстрый медианный фильтр на локальных гистограммах
# ============================================================

def _median_hist_strip(args):
    strip, ksize = args
    r = ksize // 2
    h, w = strip.shape
    padded = np.pad(strip, ((r, r), (r, r)), mode="edge")

    # вид на все окна: (h, w, ksize, ksize)
    windows = sliding_window_view(padded, (ksize, ksize))

    # сортируем значения в каждом окне — C-операция
    # сортировка по последним двум осям, берём медиану
    sorted_windows = np.sort(windows.reshape(h, w, -1), axis=2)
    median = sorted_windows[:, :, ksize * ksize // 2]

    return median.astype(np.uint8)


def apply_fast_median_filter(app, n_jobs=4):
    """Быстрый медианный фильтр на локальных гистограммах.

    Читает параметры из app.median_size_var.
    Применяется к каналу Y модели YUV.
    """
    if not app.original_image:
        messagebox.showerror("Ошибка", "Нет изображения")
        return

    ksize = int(app.median_size_var.get())
    if ksize < 1:
        messagebox.showerror("Ошибка", "Размер окна должен быть ≥ 1")
        return

    rgb_array = np.array(app.original_image.convert("RGB"))
    Y, U, V = rgb_to_yuv_manual(rgb_array)
    Y = Y.astype(np.uint8)

    strips = _split_into_strips(Y, n_jobs)
    args = [(strip, ksize) for strip in strips]

    with Pool(n_jobs) as pool:
        results = pool.map(_median_hist_strip, args)

    Y_new = np.concatenate(results, axis=0).astype(np.float32)
    rgb_new = yuv_to_rgb_manual(Y_new, U, V)

    app.processed_image = Image.fromarray(rgb_new)
    app.display_images()