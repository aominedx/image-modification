
import numpy as np
import cv2
from PIL import Image
from tkinter import messagebox

from core.color_models import rgb_to_hsv_manual, rgb_to_yuv_manual, yuv_to_rgb_manual


def update_channel_list(app, event=None):
    color_space = app.color_var.get()

    if color_space == "RGB":
        app.channel_combo["values"] = ["R", "G", "B"]
        app.channel_var.set("R")
    elif color_space == "HSV":
        app.channel_combo["values"] = ["H", "S", "V"]
        app.channel_var.set("H")
    elif color_space == "YUV":
        app.channel_combo["values"] = ["Y", "U", "V", "UV"]
        app.channel_var.set("Y")


def show_channel(app):
    if not app.original_image:
        messagebox.showerror("Ошибка", "Нет изображения")
        return

    color_space = app.color_var.get()
    channel = app.channel_var.get()

    rgb_image = app.original_image.convert("RGB")
    rgb_array = np.array(rgb_image)

    try:
        if color_space == "RGB":
            channel_array = _rgb_channel(rgb_array, channel)
        elif color_space == "HSV":
            channel_array = _hsv_channel(rgb_array, channel)
        elif color_space == "YUV":
            channel_array = _yuv_channel(rgb_array, channel)
        else:
            return

        if channel_array is None:
            return

        app.processed_image = Image.fromarray(channel_array)
        app.display_images()

    except Exception as e:
        messagebox.showerror("Ошибка", f"Ошибка отображения канала: {e}")


def _rgb_channel(rgb_array, channel):
    channel_array = np.zeros_like(rgb_array)
    idx = {"R": 0, "G": 1, "B": 2}.get(channel)
    if idx is None:
        return None
    channel_array[:, :, idx] = rgb_array[:, :, idx]
    return channel_array


def _hsv_channel(rgb_array, channel):
    H, S, V = rgb_to_hsv_manual(rgb_array)
    if channel == "H":
        H_norm = (H / 360 * 179).astype(np.uint8)
        hsv_color = np.zeros((H.shape[0], H.shape[1], 3), dtype=np.uint8)
        hsv_color[:, :, 0] = H_norm
        hsv_color[:, :, 1] = 255
        hsv_color[:, :, 2] = 255
        return cv2.cvtColor(hsv_color, cv2.COLOR_HSV2RGB)
    if channel == "S":
        return (S * 255).astype(np.uint8)
    if channel == "V":
        return (V * 255).astype(np.uint8)
    return None


def _yuv_channel(rgb_array, channel):
    Y, U, V = rgb_to_yuv_manual(rgb_array)

    if channel == "Y":
        return Y.astype(np.uint8)

    if channel == "U":
        Y_temp = np.full_like(Y, 128.0)
        V_temp = np.full_like(V, 128.0)
        return yuv_to_rgb_manual(Y_temp, U.astype(np.float32), V_temp)

    if channel == "V":
        Y_temp = np.full_like(Y, 128.0)
        U_temp = np.full_like(U, 128.0)
        return yuv_to_rgb_manual(Y_temp, U_temp, V.astype(np.float32))

    if channel == "UV":
        Y_temp = np.full_like(Y, 128.0)
        return yuv_to_rgb_manual(Y_temp, U.astype(np.float32), V.astype(np.float32))

    return None