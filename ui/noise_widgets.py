"""Виджеты для наложения шумов."""
import tkinter as tk
from tkinter import ttk


def create_noise_widgets(parent, app):
    frame = ttk.LabelFrame(parent, text="Наложение шумов")
    frame.pack(fill=tk.X, padx=5, pady=5)

    # --- тип шума ---
    ttk.Label(frame, text="Тип:").grid(row=0, column=0, sticky="w", padx=5)
    app.noise_type_var = tk.StringVar(value="impulse")
    ttk.Combobox(
        frame, textvariable=app.noise_type_var, width=16, state="readonly",
        values=["impulse", "additive", "multiplicative"],
    ).grid(row=0, column=1, padx=5)

    # --- цветовая модель ---
    ttk.Label(frame, text="Модель:").grid(row=0, column=2, sticky="w", padx=5)
    app.noise_color_var = tk.StringVar(value="RGB")
    noise_color_combo = ttk.Combobox(
        frame, textvariable=app.noise_color_var, width=6, state="readonly",
        values=["RGB", "HSV", "YUV"],
    )
    noise_color_combo.grid(row=0, column=3, padx=5)

    # --- канал ---
    ttk.Label(frame, text="Канал:").grid(row=0, column=4, sticky="w", padx=5)
    app.noise_channel_var = tk.StringVar(value="R")
    app.noise_channel_combo = ttk.Combobox(
        frame, textvariable=app.noise_channel_var, width=5, state="readonly",
        values=["R", "G", "B"],
    )
    app.noise_channel_combo.grid(row=0, column=5, padx=5)

    # при смене модели — обновляем список каналов
    noise_color_combo.bind(
        "<<ComboboxSelected>>",
        lambda e: _update_noise_channels(app),
    )

    # --- уровень зашумлённости (импульсный) ---
    ttk.Label(frame, text="Уровень, %:").grid(row=1, column=0, sticky="w", padx=5, pady=3)
    app.noise_level_var = tk.DoubleVar(value=10.0)
    ttk.Scale(
        frame, from_=0.0, to=100.0, variable=app.noise_level_var,
        orient=tk.HORIZONTAL, length=180,
    ).grid(row=1, column=1, columnspan=2, padx=5, sticky="we")

    # --- коэффициент распределения импульсов ---
    ttk.Label(frame, text="Баланс бел/чёрн:").grid(row=1, column=3, sticky="w", padx=5)
    app.noise_balance_var = tk.DoubleVar(value=0.5)
    ttk.Scale(
        frame, from_=0.0, to=1.0, variable=app.noise_balance_var,
        orient=tk.HORIZONTAL, length=140,
    ).grid(row=1, column=4, columnspan=2, padx=5, sticky="we")

    # --- диапазон KMin / KMax для аддитивного и мультипликативного ---
    ttk.Label(frame, text="KMin:").grid(row=2, column=0, sticky="w", padx=5, pady=3)
    app.noise_kmin_var = tk.DoubleVar(value=-50.0)
    ttk.Entry(frame, textvariable=app.noise_kmin_var, width=10).grid(row=2, column=1, padx=5)

    ttk.Label(frame, text="KMax:").grid(row=2, column=2, sticky="w", padx=5)
    app.noise_kmax_var = tk.DoubleVar(value=50.0)
    ttk.Entry(frame, textvariable=app.noise_kmax_var, width=10).grid(row=2, column=3, padx=5)

    # --- кнопка применения ---
    ttk.Button(
        frame, text="Наложить шум", command=app.add_noise,
    ).grid(row=3, column=0, columnspan=6, pady=6)

    _update_noise_channels(app)


def _update_noise_channels(app):
    """Обновляет список каналов в зависимости от выбранной в блоке шума модели."""
    cs = app.noise_color_var.get()
    if cs == "RGB":
        values = ["R", "G", "B"]
        default = "R"
    elif cs == "HSV":
        values = ["H", "S", "V"]
        default = "H"
    else:  # YUV
        values = ["Y", "U", "V"]
        default = "Y"

    app.noise_channel_combo["values"] = values
    app.noise_channel_var.set(default)