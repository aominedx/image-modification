"""Наложение шумов на каналы изображения (импульсный, аддитивный, мультипликативный)."""
import numpy as np
from PIL import Image
from tkinter import messagebox

from core.color_models import rgb_to_hsv_manual, rgb_to_yuv_manual, yuv_to_rgb_manual


# ============================================================
# RGB <-> выбранная модель: разложение на каналы и сборка обратно
# ============================================================

def _split_channels(rgb_array, color_space):
    """Возвращает dict {имя_канала: массив float32} для нужной модели.

    Для HSV канал H — в градусах [0, 360), S и V — в [0, 1].
    Для YUV все каналы в [0, 255].
    """
    if color_space == "RGB":
        R = rgb_array[:, :, 0].astype(np.float32)
        G = rgb_array[:, :, 1].astype(np.float32)
        B = rgb_array[:, :, 2].astype(np.float32)
        return {"R": R, "G": G, "B": B}

    if color_space == "HSV":
        H, S, V = rgb_to_hsv_manual(rgb_array)
        return {"H": H.astype(np.float32),
                "S": S.astype(np.float32),
                "V": V.astype(np.float32)}

    if color_space == "YUV":
        Y, U, V = rgb_to_yuv_manual(rgb_array)
        return {"Y": Y.astype(np.float32),
                "U": U.astype(np.float32),
                "V": V.astype(np.float32)}

    return {}


def _merge_channels(channels, color_space):
    """Собирает изображение RGB из dict каналов."""
    if color_space == "RGB":
        R = np.clip(channels["R"], 0, 255)
        G = np.clip(channels["G"], 0, 255)
        B = np.clip(channels["B"], 0, 255)
        return np.stack([R, G, B], axis=2).astype(np.uint8)

    if color_space == "HSV":
        H = np.mod(channels["H"], 360.0)          # H цикличен по 360°
        S = np.clip(channels["S"], 0, 1)
        V = np.clip(channels["V"], 0, 1)
        # HSV -> RGB вручную (без cv2), чтобы не тащить зависимость
        return _hsv_to_rgb(H, S, V)

    if color_space == "YUV":
        Y = np.clip(channels["Y"], 0, 255).astype(np.float32)
        U = np.clip(channels["U"], 0, 255).astype(np.float32)
        V = np.clip(channels["V"], 0, 255).astype(np.float32)
        return yuv_to_rgb_manual(Y, U, V)

    return None


def _hsv_to_rgb(H, S, V):
    """HSV (H: 0-360, S,V: 0-1) → RGB uint8."""
    C = V * S
    Hp = H / 60.0
    X = C * (1 - np.abs(np.mod(Hp, 2) - 1))
    m = V - C

    R1 = np.zeros_like(H)
    G1 = np.zeros_like(H)
    B1 = np.zeros_like(H)

    mask = (0 <= Hp) & (Hp < 1)
    R1[mask], G1[mask], B1[mask] = C[mask], X[mask], 0
    mask = (1 <= Hp) & (Hp < 2)
    R1[mask], G1[mask], B1[mask] = X[mask], C[mask], 0
    mask = (2 <= Hp) & (Hp < 3)
    R1[mask], G1[mask], B1[mask] = 0, C[mask], X[mask]
    mask = (3 <= Hp) & (Hp < 4)
    R1[mask], G1[mask], B1[mask] = 0, X[mask], C[mask]
    mask = (4 <= Hp) & (Hp < 5)
    R1[mask], G1[mask], B1[mask] = X[mask], 0, C[mask]
    mask = (5 <= Hp) & (Hp < 6)
    R1[mask], G1[mask], B1[mask] = C[mask], 0, X[mask]

    R = np.clip((R1 + m) * 255, 0, 255)
    G = np.clip((G1 + m) * 255, 0, 255)
    B = np.clip((B1 + m) * 255, 0, 255)
    return np.stack([R, G, B], axis=2).astype(np.uint8)


# ============================================================
# Импульсный шум
# ============================================================

def _apply_impulse_noise(channel, level_percent, balance, color_space, channel_name):
    """Импульсный шум: доля пикселей заменяется на «белые» или «чёрные» импульсы.

    level_percent — процент зашумлённых пикселей от площади изображения [0, 100].
    balance       — коэффициент распределения импульсов: доля белых импульсов [0, 1].
                    balance=0 → все импульсы чёрные, balance=1 → все белые.
    Для канала H (HSV) импульсы — это ±180° (уход в противоположный оттенок).
    Для каналов S и V (HSV) «белый» = 1.0, «чёрный» = 0.0.
    Для YUV и RGB «белый» = 255, «чёрный» = 0.
    """
    h, w = channel.shape
    n_pixels = h * w
    n_noisy = int(n_pixels * level_percent / 100.0)
    if n_noisy == 0:
        return channel

    # выбираем случайные позиции без повторений
    flat_idx = np.random.choice(n_pixels, size=n_noisy, replace=False)
    ys, xs = np.unravel_index(flat_idx, (h, w))

    # делим на «белые» и «чёрные» согласно balance
    n_white = int(n_noisy * balance)
    white_idx = slice(0, n_white)
    black_idx = slice(n_white, n_noisy)

    # определяем «белое» и «чёрное» значение для этого канала
    if color_space == "HSV" and channel_name == "H":
        white_val, black_val = None, None  # обрабатываем отдельно (нужен ±180)
    elif color_space == "HSV":
        white_val, black_val = 1.0, 0.0
    else:
        white_val, black_val = 255.0, 0.0

    # белые импульсы
    if n_white > 0:
        wy, wx = ys[white_idx], xs[white_idx]
        if color_space == "HSV" and channel_name == "H":
            channel[wy, wx] = np.mod(channel[wy, wx] + 180.0, 360.0)
        else:
            channel[wy, wx] = white_val

    # чёрные импульсы
    if n_noisy - n_white > 0:
        by, bx = ys[black_idx], xs[black_idx]
        if color_space == "HSV" and channel_name == "H":
            channel[by, bx] = np.mod(channel[by, bx] + 180.0, 360.0)
        else:
            channel[by, bx] = black_val

    return channel


# ============================================================
# Аддитивный шум
# ============================================================

def _apply_additive_noise(channel, k_min, k_max, color_space, channel_name):
    """Аддитивный шум: к каналу прибавляется случайная величина из [k_min, k_max].

    Для канала H (HSV) величина прибавляется в градусах и результат берётся по модулю 360.
    Для S и V (HSV) диапазон интерпретируется в единицах [0, 1] — то есть [k_min/255, k_max/255],
    чтобы пользователь задавал значения в привычной шкале.
    """
    h, w = channel.shape
    noise = np.random.uniform(k_min, k_max, size=(h, w)).astype(np.float32)

    if color_space == "HSV":
        if channel_name == "H":
            channel = np.mod(channel + noise, 360.0)
        else:
            # S и V живут в [0, 1]; переводим шум из 0-255 в 0-1
            channel = channel + noise / 255.0
        return channel

    return channel + noise


# ============================================================
# Мультипликативный шум
# ============================================================

def _apply_multiplicative_noise(channel, k_min, k_max, color_space, channel_name):
    """Мультипликативный шум: канал умножается на случайный коэффициент из [k_min, k_max].

    Для канала H (HSV) коэффициент применяется не к градусам, а к «сдвигу»:
    новый H = H * k (по модулю 360), что меняет оттенок.
    """
    h, w = channel.shape
    factor = np.random.uniform(k_min, k_max, size=(h, w)).astype(np.float32)

    if color_space == "HSV" and channel_name == "H":
        return np.mod(channel * factor, 360.0)

    return channel * factor


# ============================================================
# Публичная функция
# ============================================================

def add_noise(app,
              noise_type="impulse",
              color_space="RGB",
              channel_name="R",
              level_percent=10.0,
              balance=0.5,
              k_min=-50.0,
              k_max=50.0):
    """Наложение шума на выбранный канал изображения.

    Параметры:
      noise_type      : "impulse" | "additive" | "multiplicative"
      color_space     : "RGB" | "HSV" | "YUV"
      channel_name    : имя канала в выбранной модели
      level_percent   : % зашумлённых пикселей (только импульсный)
      balance         : доля белых импульсов [0, 1] (только импульсный)
      k_min, k_max    : диапазон значений шума (аддитивный, мультипликативный)
    """
    if not app.original_image:
        messagebox.showerror("Ошибка", "Нет изображения")
        return

    rgb_array = np.array(app.original_image.convert("RGB"))
    channels = _split_channels(rgb_array, color_space)

    if channel_name not in channels:
        messagebox.showerror("Ошибка", f"Канал {channel_name} не найден в модели {color_space}")
        return

    ch = channels[channel_name].copy()

    if noise_type == "impulse":
        ch = _apply_impulse_noise(ch, level_percent, balance, color_space, channel_name)
    elif noise_type == "additive":
        ch = _apply_additive_noise(ch, k_min, k_max, color_space, channel_name)
    elif noise_type == "multiplicative":
        ch = _apply_multiplicative_noise(ch, k_min, k_max, color_space, channel_name)
    else:
        messagebox.showerror("Ошибка", f"Неизвестный тип шума: {noise_type}")
        return

    channels[channel_name] = ch
    rgb_noisy = _merge_channels(channels, color_space)

    app.processed_image = Image.fromarray(rgb_noisy)
    app.base_image = app.processed_image.copy()  # чтобы последующие операции работали от зашумлённого
    app.display_images()