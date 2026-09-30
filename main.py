
import tkinter as tk

from ui.app import ImageProcessor


def main():
    root = tk.Tk()
    app = ImageProcessor(root)
    root.mainloop()


if __name__ == "__main__":
    main()