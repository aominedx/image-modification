
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
from tkinter import messagebox, simpledialog
from multiprocessing import Pool

from core.color_models import rgb_to_yuv_manual, yuv_to_rgb_manual
from time_work import time_work



def _partial_histogram(chunk):
    """Строит гистограмму для одного фрагмента (приватная гистограмма)."""
    hist = np.zeros(256, dtype=np.int64)
    for value in chunk:
        hist[value] += 1
    return hist


def _partial_stats(chunk):
    """Минимум, максимум, сумма, размер для фрагмента."""
    return int(chunk.min()), int(chunk.max()), int(chunk.sum()), int(chunk.size)


def _apply_lut_chunk(args):
    """Применяет LUT к фрагменту."""
    chunk, lut = args
    return lut[chunk]


# def _apply_parabola_chunk(args):
#     """Применяет параболу BCET к фрагменту."""
#     chunk, a, b, c = args
#     val = a * (chunk.astype(np.float32) - b) ** 2 + c
#     return np.clip(val, 0, 255).astype(np.uint8)
#
#
# def _apply_gamma_chunk(args):
#     """Применяет гамма-коррекцию к фрагменту."""
#     chunk, gamma = args
#     norm = chunk.astype(np.float32) / 255.0
#     val = 255.0 * np.power(norm, 1/gamma)
#     return np.clip(val, 0, 255).astype(np.uint8)

def _build_bcet_lut(a, b, c):
    """Y = a*(Y-b)^2 + c."""
    y = np.arange(256, dtype=np.float32)
    lut = a * (y - b) ** 2 + c
    return np.clip(lut, 0, 255).astype(np.uint8)


def _build_gamma_lut(gamma):
    """ Y = 255*(Y/255)^(1/gamma)"""
    y = np.arange(256, dtype=np.float32)
    lut = 255.0 * np.power(y / 255.0, 1/gamma)
    return np.clip(lut, 0, 255).astype(np.uint8)

#@time_work()
def bcet_correction(app, n_jobs=4):
    """Параллельная BCET-коррекция через LUT."""
    if not app.original_image:
        messagebox.showerror("Ошибка", "Нет изображения")
        return
    print(f"Количество потоков - {n_jobs}")

    rgb_array = np.array(app.original_image.convert("RGB"))
    Y, U, V = rgb_to_yuv_manual(rgb_array)
    Y = Y.astype(np.float32)

    h, w = Y.shape
    flat = Y.ravel()
    chunks = np.array_split(flat, n_jobs)

    with Pool(n_jobs) as pool:
        stats = pool.map(_partial_stats, chunks)

    Y_min = float(min(s[0] for s in stats))
    Y_max = float(max(s[1] for s in stats))
    total = sum(s[3] for s in stats)
    Y_mean = sum(s[2] for s in stats) / total

    if Y_max == Y_min:
        messagebox.showinfo("Инфо", "Изображение однородное, BCET не нужен")
        return

    target_min, target_max, target_mean = 0.0, 255.0, 128.0

    k = (target_max - target_min) / (target_mean - target_min)
    num = k * (Y_mean - Y_min) * (Y_mean + Y_min) - (Y_max - Y_min) * (Y_max + Y_min)
    den = 2 * (k * (Y_mean - Y_min) - (Y_max - Y_min))
    if abs(den) < 1e-6:
        messagebox.showinfo("Инфо", "BCET невозможен")
        return

    b = num / den
    if abs((Y_max - b) ** 2 - (Y_min - b) ** 2) < 1e-6:
        messagebox.showinfo("Инфо", "BCET невозможен")
        return

    a = (target_max - target_min) / ((Y_max - b) ** 2 - (Y_min - b) ** 2)
    c = target_min - a * (Y_min - b) ** 2
    # if a > 255: a = 255
    # if b > 255: b = 255
    # if c > 255: c = 255
    # if a < 0: a = 0
    # if b < 0: b = 0
    # if c < 0: c = 0
    #  LUT
    lut = _build_bcet_lut(a, b, c)

    #  параллельное применение LUT
    Y_uint8 = Y.astype(np.uint8)
    flat_u8 = Y_uint8.ravel()
    chunks_u8 = np.array_split(flat_u8, n_jobs)
    args = [(chunk, lut) for chunk in chunks_u8]

    with Pool(n_jobs) as pool:
        results = pool.map(_apply_lut_chunk, args)

    Y_new = np.concatenate(results, axis=0).reshape(h, w).astype(np.float32)
    rgb_new = yuv_to_rgb_manual(Y_new, U, V)

    app.processed_image = Image.fromarray(rgb_new)
    app.display_images()

#@time_work()
def gamma_correction(app, n_jobs=4, gamma=None):

    if not app.original_image:
        messagebox.showerror("Ошибка", "Нет изображения")
        return

    print(f"Количество потоков - {n_jobs}")

    if gamma is None:
        gamma = simpledialog.askfloat(
            "Gamma", "Введите gamma (0.1 - 3.0):",
            initialvalue=1.0, minvalue=0.1, maxvalue=3.0,
        )
        if gamma is None:
            return

    rgb_array = np.array(app.original_image.convert("RGB"))
    Y, U, V = rgb_to_yuv_manual(rgb_array)
    Y_uint8 = Y.astype(np.uint8)

    h, w = Y_uint8.shape
    flat = Y_uint8.ravel()
    chunks = np.array_split(flat, n_jobs)

    # --- строим LUT один раз ---
    lut = _build_gamma_lut(gamma)

    # --- параллельно применяем ---
    args = [(chunk, lut) for chunk in chunks]

    with Pool(n_jobs) as pool:
        results = pool.map(_apply_lut_chunk, args)

    Y_new = np.concatenate(results, axis=0).reshape(h, w).astype(np.float32)
    rgb_new = yuv_to_rgb_manual(Y_new, U, V)

    app.processed_image = Image.fromarray(rgb_new)
    app.display_images()

def show_histogram(app):
    """Построение гистограммы выбранного канала (без параллелизма — визуализация)."""
    if not app.original_image:
        messagebox.showerror("Ошибка", "Нет изображения")
        return

    color_space = app.color_var.get()
    channel = app.channel_var.get()
    rgb_array = np.array(app.original_image.convert("RGB"))

    try:
        channel_array = _extract_channel(rgb_array, color_space, channel)
        if channel_array is None:
            return

        fig, ax = plt.subplots(figsize=(6, 4))
        ax.hist(channel_array.ravel(), bins=256, range=(0, 256), color="steelblue")
        ax.set_title(f"Гистограмма канала {channel} ({color_space})")
        ax.set_xlabel("Значение пикселя")
        ax.set_ylabel("Количество пикселей")
        plt.show()

    except Exception as e:
        messagebox.showerror("Ошибка", f"Ошибка построения гистограммы: {e}")


def _extract_channel(rgb_array, color_space, channel):
    if color_space == "RGB":
        idx = {"R": 0, "G": 1, "B": 2}.get(channel)
        if idx is None:
            return None
        return rgb_array[:, :, idx]

    if color_space == "HSV":
        from core.color_models import rgb_to_hsv_manual
        H, S, V = rgb_to_hsv_manual(rgb_array)
        if channel == "H":
            return (H / 360 * 255).astype(np.uint8)
        if channel == "S":
            return (S * 255).astype(np.uint8)
        if channel == "V":
            return (V * 255).astype(np.uint8)
        return None

    if color_space == "YUV":
        Y, U, V = rgb_to_yuv_manual(rgb_array)
        if channel == "Y":
            return Y.astype(np.uint8)
        if channel == "U":
            return U.astype(np.uint8)
        if channel == "V":
            return V.astype(np.uint8)
        if channel == "UV":
            return ((U.astype(np.float32) + V.astype(np.float32)) / 2).astype(np.uint8)
        return None

    return None



def equalize_histogram(app, n_jobs=4):
    if not app.original_image:
        messagebox.showerror("Ошибка", "Нет изображения")
        return

    rgb_array = np.array(app.original_image.convert("RGB"))
    Y, U, V = rgb_to_yuv_manual(rgb_array)
    Y = Y.astype(np.uint8)

    flat = Y.ravel()
    chunks = np.array_split(flat, n_jobs)

    with Pool(n_jobs) as pool:
        partials = pool.map(_partial_histogram, chunks)

    hist = np.sum(partials, axis=0)

    cdf = hist.cumsum()
    cdf_min = cdf.min()
    total = flat.size
    cdf_norm = (cdf - cdf_min) / (total - cdf_min) * 255
    cdf_norm = np.clip(cdf_norm, 0, 255).astype(np.uint8)

    args = [(chunk, cdf_norm) for chunk in chunks]

    with Pool(n_jobs) as pool:
        results = pool.map(_apply_lut_chunk, args)

    Y_eq = np.concatenate(results, axis=0).reshape(Y.shape)
    rgb_new = yuv_to_rgb_manual(Y_eq.astype(np.float32), U, V)

    app.processed_image = Image.fromarray(rgb_new)
    app.display_images()
