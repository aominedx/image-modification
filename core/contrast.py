
import numpy as np
from PIL import Image
from tkinter import messagebox
from multiprocessing import Pool


def _build_contrast_lut(contrast_factor, brightness_factor):
    y = np.arange(256, dtype=np.float32)
    lut = contrast_factor * (y - 128.0) + 128.0 + (brightness_factor - 1.0) * 128.0
    return np.clip(lut, 0, 255).astype(np.uint8)


def _apply_lut_chunk(args):
    chunk, lut = args
    return lut[chunk]


def _process_chunk(args):
    chunk, lut = args

    # --- 1. RGB → YUV ---
    R = chunk[:, 0].astype(np.float32)
    G = chunk[:, 1].astype(np.float32)
    B = chunk[:, 2].astype(np.float32)

    Y = 0.299 * R + 0.587 * G + 0.114 * B
    U = -0.14713 * R - 0.28886 * G + 0.436 * B + 128.0
    V = 0.615 * R - 0.51499 * G - 0.10001 * B + 128.0

    # --- 2. коррекция Y через LUT ---
    # LUT индексируется целочисленными значениями, поэтому округляем Y
    Y_u8 = np.clip(Y, 0, 255).astype(np.uint8)
    Y_new = lut[Y_u8].astype(np.float32)

    # --- 3. YUV → RGB ---
    u = U - 128.0
    v = V - 128.0

    R_new = Y_new + 1.13983 * v
    G_new = Y_new - 0.39465 * u - 0.58060 * v
    B_new = Y_new + 2.03211 * u

    result = np.stack([
        np.clip(R_new, 0, 255),
        np.clip(G_new, 0, 255),
        np.clip(B_new, 0, 255),
    ], axis=1)

    return result.astype(np.uint8)


def adjust_contrast_brightness(app, n_jobs=4):
    if not app.original_image:
        messagebox.showerror("Ошибка", "Нет изображения")
        return

    contrast_factor = app.contrast_var.get()
    brightness_factor = app.brightness_var.get()

    lut = _build_contrast_lut(contrast_factor, brightness_factor)

    rgb_array = np.array(app.base_image.convert("RGB"))
    h, w, _ = rgb_array.shape

    flat = rgb_array.reshape(-1, 3)
    chunks = np.array_split(flat, n_jobs)

    args = [(chunk, lut) for chunk in chunks]

    with Pool(n_jobs) as pool:
        results = pool.map(_process_chunk, args)

    output = np.concatenate(results, axis=0).reshape(h, w, 3)

    app.processed_image = Image.fromarray(output)
    app.display_images()