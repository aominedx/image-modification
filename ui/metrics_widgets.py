"""Виджеты для сравнения фильтров."""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv


def create_metrics_widgets(parent, app):
    frame = ttk.LabelFrame(parent, text="Сравнение качества обработки")
    frame.pack(fill=tk.X, padx=5, pady=5)

    ttk.Label(frame, text="Метрики:").grid(row=0, column=0, sticky="w", padx=3)
    app.metrics_space_var = tk.StringVar(value="YUV (Y)")
    ttk.Combobox(
        frame, textvariable=app.metrics_space_var, width=10, state="readonly",
        values=["YUV (Y)", "RGB"],
    ).grid(row=0, column=1, padx=3)

    ttk.Label(frame, text="Прогонов:").grid(row=0, column=2, sticky="w", padx=3)
    app.metrics_runs_var = tk.IntVar(value=5)
    ttk.Spinbox(frame, from_=1, to=50, textvariable=app.metrics_runs_var,
                width=4).grid(row=0, column=3, padx=3)

    ttk.Button(frame, text="Сравнить фильтры",
               command=app.compare_filters).grid(
        row=1, column=0, columnspan=2, pady=4)
    ttk.Button(frame, text="Сохранить отчёт (CSV)",
               command=app.save_metrics_report).grid(
        row=1, column=2, columnspan=2, pady=4)

    ttk.Button(frame, text="Сохранить графики",
               command=app.save_metrics_graphs).grid(
        row=2, column=0, columnspan=4, pady=4)

def show_metrics_report(parent, results):
    """Показывает таблицу с результатами в отдельном окне."""
    win = tk.Toplevel(parent)
    win.title("Сравнение фильтров")

    cols = ("name", "MSE", "PSNR", "Delta", "time_ms", "time_ci")
    headers = ("Фильтр", "MSE", "PSNR, дБ", "Delta", "Время, мс", "±CI, мс")

    tree = ttk.Treeview(win, columns=cols, show="headings", height=12)
    for c, h in zip(cols, headers):
        tree.heading(c, text=h)
        tree.column(c, width=140, anchor="center")
    tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    for r in results:
        tree.insert("", tk.END, values=(
            r["name"],
            f"{r['MSE']:.2f}",
            f"{r['PSNR']:.2f}" if r["PSNR"] != float("inf") else "∞",
            f"{r['Delta']:.2f}",
            f"{r['time_ms']:.2f}",
            f"{r['time_ci']:.2f}",
        ))


def save_metrics_csv(parent, results):
    """Сохраняет результаты в CSV-файл."""
    path = filedialog.asksaveasfilename(
        title="Сохранить отчёт",
        defaultextension=".csv",
        filetypes=[("CSV", "*.csv"), ("Все файлы", "*.*")],
    )
    if not path:
        return

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(["Фильтр", "MSE", "PSNR (дБ)", "Delta", "Время (мс)", "CI (мс)"])
        for r in results:
            writer.writerow([
                r["name"],
                f"{r['MSE']:.4f}",
                f"{r['PSNR']:.4f}" if r["PSNR"] != float("inf") else "inf",
                f"{r['Delta']:.4f}",
                f"{r['time_ms']:.4f}",
                f"{r['time_ci']:.4f}",
            ])

    messagebox.showinfo("Готово", f"Отчёт сохранён: {path}")

def save_metrics_report(app):
    """Сохраняет результаты сравнения в CSV-файл.

    Берёт результаты из app.metrics_results.
    """
    from tkinter import filedialog, messagebox
    import csv

    results = getattr(app, "metrics_results", None)
    if not results:
        messagebox.showerror("Ошибка", "Сначала выполните сравнение")
        return

    path = filedialog.asksaveasfilename(
        title="Сохранить отчёт",
        defaultextension=".csv",
        filetypes=[("CSV", "*.csv"), ("Все файлы", "*.*")],
    )
    if not path:
        return

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(["Фильтр", "MSE", "PSNR (дБ)", "Delta", "Время (мс)", "CI (мс)"])
        for r in results:
            writer.writerow([
                r["name"],
                f"{r['MSE']:.4f}",
                f"{r['PSNR']:.4f}" if r["PSNR"] != float("inf") else "inf",
                f"{r['Delta']:.4f}",
                f"{r['time_ms']:.4f}",
                f"{r['time_ci']:.4f}",
            ])

    messagebox.showinfo("Готово", f"Отчёт сохранён: {path}")