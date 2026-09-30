
import numpy as np
from PIL import Image
from tkinter import messagebox


def rgb_to_hsv_manual(rgb_array):
    """RGB → HSV (H: 0-360, S: 0-1, V: 0-1)."""
    rgb_norm = rgb_array.astype(np.float32) / 255.0
    R = rgb_norm[:, :, 0]
    G = rgb_norm[:, :, 1]
    B = rgb_norm[:, :, 2]

    Cmax = np.max(rgb_norm, axis=2)
    Cmin = np.min(rgb_norm, axis=2)
    delta = Cmax - Cmin

    H = np.zeros_like(Cmax)
    mask_r = (Cmax == R) & (delta != 0)
    H[mask_r] = (60 * ((G[mask_r] - B[mask_r]) / delta[mask_r])) % 360

    mask_g = (Cmax == G) & (delta != 0)
    H[mask_g] = 60 * ((B[mask_g] - R[mask_g]) / delta[mask_g]) + 120

    mask_b = (Cmax == B) & (delta != 0)
    H[mask_b] = 60 * ((R[mask_b] - G[mask_b]) / delta[mask_b]) + 240

    S = np.zeros_like(Cmax)
    mask_s = Cmax != 0
    S[mask_s] = delta[mask_s] / Cmax[mask_s]

    V = Cmax
    return H, S, V


def rgb_to_yuv_manual(rgb_array):
    """RGB → YUV (BT.601)."""
    rgb_float = rgb_array.astype(np.float32)
    R = rgb_float[:, :, 0]
    G = rgb_float[:, :, 1]
    B = rgb_float[:, :, 2]

    Y = 0.299 * R + 0.587 * G + 0.114 * B
    U = -0.14713 * R - 0.28886 * G + 0.436 * B + 128
    V = 0.615 * R - 0.51499 * G - 0.10001 * B + 128

    Y = np.clip(Y, 0, 255)
    U = np.clip(U, 0, 255)
    V = np.clip(V, 0, 255)
    return Y, U, V


def yuv_to_rgb_manual(Y, U, V):
    """YUV → RGB (BT.601)."""
    Y = Y.astype(np.float32)
    U = U.astype(np.float32) - 128.0
    V = V.astype(np.float32) - 128.0

    R = Y + 1.13983 * V
    G = Y - 0.39465 * U - 0.58060 * V
    B = Y + 2.03211 * U

    R = np.clip(R, 0, 255)
    G = np.clip(G, 0, 255)
    B = np.clip(B, 0, 255)

    return np.stack([R, G, B], axis=2).astype(np.uint8)


def convert_color_space(app):
    if not app.original_image:
        messagebox.showerror("Ошибка", "Нет изображения")
        return

    color_space = app.color_var.get()
    rgb_image = app.original_image.convert("RGB")
    rgb_array = np.array(rgb_image)

    try:
        if color_space == "HSV":
            H, S, V = rgb_to_hsv_manual(rgb_array)
            H_vis = (H / 360 * 255).astype(np.uint8)
            S_vis = (S * 255).astype(np.uint8)
            V_vis = (V * 255).astype(np.uint8)
            hsv_vis = np.stack([H_vis, S_vis, V_vis], axis=2)
            app.processed_image = Image.fromarray(hsv_vis)
            app.base_image = app.processed_image.copy()

        elif color_space == "YUV":
            Y, U, V = rgb_to_yuv_manual(rgb_array)
            yuv_vis = np.stack([Y.astype(np.uint8), U.astype(np.uint8), V.astype(np.uint8)], axis=2)
            app.processed_image = Image.fromarray(yuv_vis)
            app.base_image = app.processed_image.copy()

        else:
            app.processed_image = rgb_image.copy()
            app.base_image = app.processed_image.copy()

    except Exception as e:
        messagebox.showerror("Ошибка", f"Ошибка преобразования: {e}")
        app.processed_image = rgb_image.copy()

    app.display_images()