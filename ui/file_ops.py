
from tkinter import filedialog, messagebox

from PIL import Image, ImageTk
from time_work import time_work

def load_image(app):
    file_path = filedialog.askopenfilename(
        title="Выберите изображение",
        filetypes=[("Изображения", "*.jpg *.jpeg *.png *.bmp *.tiff")],
    )
    if not file_path:
        return
    try:
        app.original_image = Image.open(file_path)
        app.base_image = app.original_image.copy()
        app.processed_image = app.original_image.copy()
        app.display_images()
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось загрузить изображение: {e}")


def save_image(app):
    if not app.processed_image:
        messagebox.showerror("Ошибка", "Нет изображения")
        return

    file_path = filedialog.asksaveasfilename(
        title="Сохранить изображение",
        defaultextension=".png",
        filetypes=[
            ("PNG файлы", "*.png"),
            ("JPEG файлы", "*.jpg"),
            ("Все файлы", "*.*"),
        ],
    )
    if not file_path:
        return
    try:
        app.processed_image.save(file_path)
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось сохранить файл: {e}")


def reset_image(app):
    if not app.original_image:
        messagebox.showerror("Ошибка", "Нет изображения")
        return
    app.processed_image = app.original_image.copy()
    app.base_image = app.original_image.copy()
    app.display_images()


def display_images(app):
    if app.original_image:
        orig_display = app.original_image.copy()
        orig_display.thumbnail((600, 600))
        orig_photo = ImageTk.PhotoImage(orig_display)
        app.original_label.config(image=orig_photo)
        app.original_label.image = orig_photo

    if app.processed_image:
        proc_display = app.processed_image.copy()
        proc_display.thumbnail((600, 600))
        proc_photo = ImageTk.PhotoImage(proc_display)
        app.processed_label.config(image=proc_photo)
        app.processed_label.image = proc_photo