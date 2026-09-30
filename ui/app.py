
import tkinter as tk
from tkinter import ttk

from ui.widgets import (
    create_buttons,
    create_color_space_widgets,
    create_contrast_widgets,
    create_histogram_widgets,
)
from ui.file_ops import load_image, save_image, reset_image, display_images
from core.color_models import convert_color_space
from core.channels import show_channel
from core.histograms import (
    equalize_histogram,
    bcet_correction,
    gamma_correction,
    show_histogram,
)
from core.contrast import adjust_contrast_brightness

from core.noise import add_noise as _add_noise
from ui.noise_widgets import create_noise_widgets

from core.filters import apply_average_filter as _apply_average_filter
from core.filters import apply_unsharp_mask as _apply_unsharp_mask
from ui.filter_widgets import create_filter_widgets

from core.filters import apply_recursive_average_filter as _apply_recursive_average_filter
from core.filters import apply_fast_median_filter as _apply_fast_median_filter

import numpy as np
from tkinter import messagebox

from core.metrics import compare_filters as _compare_filters
from ui.metrics_widgets import create_metrics_widgets, show_metrics_report, save_metrics_csv

class ImageProcessor:
    def __init__(self, root):
        self.root = root
        self.root.title("Инструмент для обработки изображений")
        self.root.geometry("1200x800")

        self.original_image = None
        self.processed_image = None
        self.base_image = None

        # UI-переменные
        self.color_var = tk.StringVar(value="RGB")
        self.channel_var = tk.StringVar(value="R")
        self.contrast_var = tk.DoubleVar(value=1.0)
        self.brightness_var = tk.DoubleVar(value=1.0)

        self.setup_ui()

        self._metrics_results = []

    def setup_ui(self):
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # ---- левое и правое окна изображений ----
        images_frame = ttk.Frame(main_frame)
        images_frame.pack(fill=tk.BOTH, expand=True)

        self.left_frame = ttk.LabelFrame(images_frame, text="Исходное изображение")
        self.left_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        self.right_frame = ttk.LabelFrame(images_frame, text="Обработанное изображение")
        self.right_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")

        images_frame.columnconfigure(0, weight=1)
        images_frame.columnconfigure(1, weight=1)
        images_frame.rowconfigure(0, weight=1)

        self.original_label = ttk.Label(self.left_frame, text="Изображение не загружено")
        self.original_label.pack(padx=10, pady=10)

        self.processed_label = ttk.Label(
            self.right_frame,
            text="Здесь появится обработанное изображение",
        )
        self.processed_label.pack(padx=10, pady=10)

        # ---- прокручиваемая панель управления ----
        controls_outer = ttk.LabelFrame(main_frame, text="Управление")
        controls_outer.pack(fill=tk.X, padx=5, pady=5)

        canvas = tk.Canvas(controls_outer, height=260, highlightthickness=0)
        scrollbar = ttk.Scrollbar(controls_outer, orient="vertical", command=canvas.yview)
        control_frame = ttk.Frame(canvas)

        control_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=control_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.X, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # прокрутка колёсиком мыши (необязательно)
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # ---- блоки управления ----
        create_buttons(control_frame, self)
        create_color_space_widgets(control_frame, self)
        create_contrast_widgets(control_frame, self)
        create_histogram_widgets(control_frame, self)
        create_noise_widgets(control_frame, self)
        create_filter_widgets(control_frame, self)
        create_metrics_widgets(control_frame, self)

    def load_image(self):
        load_image(self)

    def save_image(self):
        save_image(self)

    def reset_image(self):
        reset_image(self)

    def display_images(self):
        display_images(self)

    def convert_color_space(self):
        convert_color_space(self)

    def update_channel_list(self, event=None):
        from core.channels import update_channel_list
        update_channel_list(self, event)

    def show_channel(self):
        show_channel(self)

    def show_histogram(self):
        show_histogram(self)

    def equalize_histogram(self):
        equalize_histogram(self)

    def bcet_correction(self):
        bcet_correction(self)

    def gamma_correction(self):
        gamma_correction(self)

    def adjust_contrast_brightness(self):
        adjust_contrast_brightness(self)

    def add_noise(self):
        _add_noise(
            self,
            noise_type=self.noise_type_var.get(),
            color_space=self.noise_color_var.get(),
            channel_name=self.noise_channel_var.get(),
            level_percent=self.noise_level_var.get(),
            balance=self.noise_balance_var.get(),
            k_min=self.noise_kmin_var.get(),
            k_max=self.noise_kmax_var.get(),
        )

    def apply_average_filter(self):
        _apply_average_filter(self)

    def apply_unsharp_mask(self):
        _apply_unsharp_mask(self)

    def apply_recursive_average_filter(self):
        _apply_recursive_average_filter(self)

    def apply_fast_median_filter(self):
        _apply_fast_median_filter(self)

    def compare_filters(self):
        _compare_filters(self)

    def save_metrics_report(self):
        _save_metrics_report(self)

    def save_metrics_graphs(self):
        if not self.metrics_results:
            messagebox.showerror("Ошибка", "Сначала выполните сравнение")
            return
        from benchmark_graphs import plot_all
        plot_all(self.metrics_results)
        messagebox.showinfo("Готово", "Графики сохранены в папку reports/")