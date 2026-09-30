
import tkinter as tk
from tkinter import ttk


def create_buttons(parent, app):
    btn_frame = ttk.Frame(parent)
    btn_frame.pack(pady=5)

    ttk.Button(btn_frame, text="Загрузить изображение", command=app.load_image).pack(side=tk.LEFT, padx=5)
    ttk.Button(btn_frame, text="Сохранить результат", command=app.save_image).pack(side=tk.LEFT, padx=5)
    ttk.Button(btn_frame, text="Сбросить изменения", command=app.reset_image).pack(side=tk.LEFT, padx=5)


def create_color_space_widgets(parent, app):
    color_frame = ttk.LabelFrame(parent, text="Преобразование цветового пространства")
    color_frame.pack(fill=tk.X, padx=5, pady=5)

    color_combo = ttk.Combobox(
        color_frame,
        textvariable=app.color_var,
        values=["RGB", "HSV", "YUV"],
    )
    color_combo.set("RGB")
    color_combo.pack(side=tk.LEFT, padx=5)
    color_combo.bind("<<ComboboxSelected>>", app.update_channel_list)

    ttk.Button(color_frame, text="Применить", command=app.convert_color_space).pack(side=tk.LEFT, padx=5)

    ttk.Label(color_frame, text="Канал:").pack(side=tk.LEFT, padx=5)

    app.channel_combo = ttk.Combobox(color_frame, textvariable=app.channel_var, width=5)
    app.channel_combo.pack(side=tk.LEFT, padx=5)

    ttk.Button(color_frame, text="Показать канал", command=app.show_channel).pack(side=tk.LEFT, padx=5)
    ttk.Button(color_frame, text="Гистограмма", command=app.show_histogram).pack(side=tk.LEFT, padx=5)

    app.update_channel_list()


def create_contrast_widgets(parent, app):
    contrast_frame = ttk.LabelFrame(parent, text="Коррекция контраста и яркости")
    contrast_frame.pack(fill=tk.X, padx=5, pady=5)

    ttk.Label(contrast_frame, text="Контраст:").pack(side=tk.LEFT, padx=5)
    ttk.Scale(
        contrast_frame,
        from_=0.1, to=3.0,
        variable=app.contrast_var,
        orient=tk.HORIZONTAL,
    ).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

    ttk.Label(contrast_frame, text="Яркость:").pack(side=tk.LEFT, padx=5)
    ttk.Scale(
        contrast_frame,
        from_=0.1, to=3.0,
        variable=app.brightness_var,
        orient=tk.HORIZONTAL,
    ).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

    ttk.Button(
        contrast_frame,
        text="Применить коррекцию",
        command=app.adjust_contrast_brightness,
    ).pack(side=tk.LEFT, padx=5)


def create_histogram_widgets(parent, app):
    hist_frame = ttk.LabelFrame(parent, text="Модификация на основе гистограмм")
    hist_frame.pack(fill=tk.X, padx=5, pady=5)

    ttk.Button(hist_frame, text="Эквализация (Y)", command=app.equalize_histogram).pack(side=tk.LEFT, padx=5)
    ttk.Button(hist_frame, text="BCET", command=app.bcet_correction).pack(side=tk.LEFT, padx=5)
    ttk.Button(hist_frame, text="Гамма-коррекция", command=app.gamma_correction).pack(side=tk.LEFT, padx=5)