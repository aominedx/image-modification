"""Виджеты для линейной фильтрации."""
import tkinter as tk
from tkinter import ttk


def create_filter_widgets(parent, app):
    frame = ttk.LabelFrame(parent, text="Линейная фильтрация")
    frame.pack(fill=tk.X, padx=5, pady=5)

    # ---------- Усредняющий фильтр ----------
    avg = ttk.LabelFrame(frame, text="Усредняющий фильтр")
    avg.pack(fill=tk.X, padx=5, pady=3)

    ttk.Label(avg, text="Модель:").grid(row=0, column=0, sticky="w", padx=3)
    app.avg_color_var = tk.StringVar(value="RGB")
    avg_color_combo = ttk.Combobox(
        avg, textvariable=app.avg_color_var, width=6, state="readonly",
        values=["RGB", "YUV"],
    )
    avg_color_combo.grid(row=0, column=1, padx=3)

    ttk.Label(avg, text="Канал:").grid(row=0, column=2, sticky="w", padx=3)
    app.avg_channel_var = tk.StringVar(value="ALL")
    app.avg_channel_combo = ttk.Combobox(
        avg, textvariable=app.avg_channel_var, width=6, state="readonly",
        values=["ALL", "R", "G", "B"],
    )
    app.avg_channel_combo.grid(row=0, column=3, padx=3)
    avg_color_combo.bind("<<ComboboxSelected>>", lambda e: _update_avg_channels(app))

    ttk.Label(avg, text="Размер:").grid(row=0, column=4, sticky="w", padx=3)
    app.avg_size_var = tk.IntVar(value=3)
    ttk.Spinbox(avg, from_=1, to=31, increment=2, textvariable=app.avg_size_var,
                width=4).grid(row=0, column=5, padx=3)

    ttk.Label(avg, text="Форма:").grid(row=0, column=6, sticky="w", padx=3)
    app.avg_shape_var = tk.StringVar(value="square")
    ttk.Combobox(
        avg, textvariable=app.avg_shape_var, width=8, state="readonly",
        values=["square", "rect", "1d"],
    ).grid(row=0, column=7, padx=3)

    ttk.Label(avg, text="Ориентация:").grid(row=0, column=8, sticky="w", padx=3)
    app.avg_orient_var = tk.StringVar(value="row")
    ttk.Combobox(
        avg, textvariable=app.avg_orient_var, width=5, state="readonly",
        values=["row", "col"],
    ).grid(row=0, column=9, padx=3)

    # ручное задание ядра
    ttk.Label(avg, text="Своё ядро (через запятую):").grid(
        row=1, column=0, columnspan=3, sticky="w", padx=3, pady=3)
    app.avg_custom_var = tk.StringVar(value="")
    ttk.Entry(avg, textvariable=app.avg_custom_var, width=40).grid(
        row=1, column=3, columnspan=5, padx=3, pady=3, sticky="we")

    ttk.Button(avg, text="Применить усреднение",
               command=app.apply_average_filter).grid(
        row=2, column=0, columnspan=10, pady=4)

    # ---------- UnsharpMask ----------
    usm = ttk.LabelFrame(frame, text="Повышение резкости (UnsharpMask, только Y в YUV)")
    usm.pack(fill=tk.X, padx=5, pady=3)

    ttk.Label(usm, text="Размер размытия:").grid(row=0, column=0, sticky="w", padx=3)
    app.usm_blur_var = tk.IntVar(value=5)
    ttk.Spinbox(usm, from_=1, to=31, increment=2, textvariable=app.usm_blur_var,
                width=4).grid(row=0, column=1, padx=3)

    ttk.Label(usm, text="Форма:").grid(row=0, column=2, sticky="w", padx=3)
    app.usm_shape_var = tk.StringVar(value="square")
    ttk.Combobox(
        usm, textvariable=app.usm_shape_var, width=8, state="readonly",
        values=["square", "rect", "1d"],
    ).grid(row=0, column=3, padx=3)

    ttk.Label(usm, text="Amount:").grid(row=0, column=4, sticky="w", padx=3)
    app.usm_amount_var = tk.DoubleVar(value=1.0)
    ttk.Entry(usm, textvariable=app.usm_amount_var, width=6).grid(row=0, column=5, padx=3)

    ttk.Label(usm, text="Threshold:").grid(row=0, column=6, sticky="w", padx=3)
    app.usm_threshold_var = tk.DoubleVar(value=0.0)
    ttk.Entry(usm, textvariable=app.usm_threshold_var, width=6).grid(row=0, column=7, padx=3)

    ttk.Label(usm, text="Своё ядро размытия:").grid(
        row=1, column=0, columnspan=2, sticky="w", padx=3, pady=3)
    app.usm_custom_var = tk.StringVar(value="")
    ttk.Entry(usm, textvariable=app.usm_custom_var, width=40).grid(
        row=1, column=2, columnspan=6, padx=3, pady=3, sticky="we")

    ttk.Button(usm, text="Применить UnsharpMask",
               command=app.apply_unsharp_mask).grid(
        row=2, column=0, columnspan=8, pady=4)

    # ---------- Рекурсивный усредняющий фильтр ----------
    rec = ttk.LabelFrame(frame, text="Рекурсивный среднеарифметический (Y в YUV)")
    rec.pack(fill=tk.X, padx=5, pady=3)

    ttk.Label(rec, text="Коэффициент α:").grid(row=0, column=0, sticky="w", padx=3)
    app.rec_alpha_var = tk.DoubleVar(value=0.5)
    ttk.Scale(rec, from_=0.0, to=0.99, variable=app.rec_alpha_var,
              orient=tk.HORIZONTAL, length=200).grid(row=0, column=1, padx=3, sticky="we")
    ttk.Label(rec, textvariable=app.rec_alpha_var).grid(row=0, column=2, padx=3)

    ttk.Button(rec, text="Применить рекурсивное усреднение",
               command=app.apply_recursive_average_filter).grid(
        row=1, column=0, columnspan=3, pady=4)

    # ---------- Быстрый медианный фильтр ----------
    med = ttk.LabelFrame(frame, text="Быстрый медианный (Y в YUV, локальные гистограммы)")
    med.pack(fill=tk.X, padx=5, pady=3)

    ttk.Label(med, text="Размер окна:").grid(row=0, column=0, sticky="w", padx=3)
    app.median_size_var = tk.IntVar(value=3)
    ttk.Spinbox(med, from_=1, to=31, increment=2,
                textvariable=app.median_size_var, width=4).grid(row=0, column=1, padx=3)

    ttk.Button(med, text="Применить медианный фильтр",
               command=app.apply_fast_median_filter).grid(
        row=1, column=0, columnspan=2, pady=4)


def _update_avg_channels(app):
    """Обновляет список каналов при смене модели в блоке усреднения."""
    cs = app.avg_color_var.get()
    if cs == "RGB":
        values = ["ALL", "R", "G", "B"]
        default = "ALL"
    else:  # YUV
        values = ["ALL", "Y", "U", "V"]
        default = "Y"
    app.avg_channel_combo["values"] = values
    app.avg_channel_var.set(default)