# Image Processing Tool

An application for color correction, noise injection, and spatial image filtering.
Features include color model conversion, histogram processing, linear and
non-linear filters, and quality assessment using specific metrics. Parallel
processing is supported.

## Features

**Color Models**
- RGB ↔ HSV and RGB ↔ YUV (BT.601) conversion — implemented manually, without OpenCV.
- Channel decomposition for the selected model with visualization.
- Channel-specific histogram generation.

**Correction**
- Brightness and contrast adjustment via the YUV model's Y channel.
- Histogram equalization, BCET, and gamma correction.
- All element-wise operations performed via LUT.

**Noise**
- Impulse noise (configurable percentage and white/black balance).
- Additive and multiplicative noise with configurable ranges.
- Impulse noise for the HSV H-channel: a ±180° shift.

**Filtering**
- Averaging filter with a custom kernel (1D, 2D).
- Recursive arithmetic mean filter.
- Fast median filter using local histograms.
- Unsharp Mask (YUV model Y-channel only).

**Quality Assessment**
- Metrics: MSE, PSNR, Delta.
- Execution time measurement with a 95% confidence interval.
- Report export to CSV and analysis charts. ## Structure

```
project/
├── main.py                  # entry point
├── time_work.py             # timing/benchmarking
├── benchmark_graphs.py      # report graphs
│
├── core/                    # algorithms
│   ├── color_models.py
│   ├── channels.py
│   ├── histograms.py
│   ├── contrast.py
│   ├── noise.py
│   ├── filters.py
│   └── metrics.py
│
└── ui/                      # Tkinter interface
├── app.py
├── widgets.py
├── file_ops.py
├── noise_widgets.py
├── filter_widgets.py
└── metrics_widgets.py
```

## Installation

```bash
git clone <repository link>
cd <folder name>

python -m venv .venv
.venv\Scripts\activate           # Windows
source .venv/bin/activate        # Linux / macOS

pip install -r requirements.txt
```

### requirements.txt

contourpy==1.4.0
cycler==0.12.1
fonttools==4.65.0
kiwisolver==1.5.1
matplotlib==3.11.2
numpy==2.5.3
opencv-python==5.0.0.93
packaging==26.3
pillow==12.3.0
pyparsing==3.3.2
python-dateutil==2.9.0.post0
six==1.17.0


OpenCV is used only for `cv2.cvtColor` when visualizing the H-channel.
All core algorithms are implemented manually using NumPy.

## Running the Application

```bash
python main.py
```

A window will open featuring two panels (original and processed images) and
a scrollable control panel.

## Usage

1. **Load Image** — select a `.jpg`, `.png`, `.bmp`, or `.tiff` file.
2. **Color Model** — select RGB, HSV, or YUV, then click "Apply".
3. **Channels** — select a channel and click "Show Channel" or "Histogram".
4. **Correction** — adjust the contrast and brightness sliders. 5. **Histogram methods** — equalization, BCET, gamma.
6. **Noise** — select type, model, and channel; configure parameters.
7. **Filters** — averaging, recursive, median, Unsharp Mask.
8. **Filter comparison** — metrics and timing, CSV export, plots.

## Technical Solutions

- **LUT** for element-wise operations — 256 values ​​instead of per-pixel recalculation.
- **NumPy vectorization** instead of Python loops: `sliding_window_view`, `einsum`,
`cumsum`, `bincount`, `frompyfunc.accumulate`.
- **Parallelism** via `multiprocessing.Pool` processing horizontal image strips.
- **Y-channel metrics** — correlate better with visual perception than RGB metrics.
- **`core/` is independent of Tkinter** — algorithms can be called from scripts and tests.
