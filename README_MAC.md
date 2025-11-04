# 🧠 NeuroFlow - CT Perfusion Auto-Analyzer (macOS)

**Automated CT Perfusion Analysis Suite for Acute Ischemic Stroke**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![PyQt5](https://img.shields.io/badge/PyQt5-5.15+-green.svg)](https://pypi.org/project/PyQt5/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-macOS-lightgrey.svg)](https://www.apple.com/macos/)

---

## 📋 Overview

NeuroFlow is a comprehensive CT Perfusion analysis tool designed for **macOS** that automates the calculation of critical stroke metrics including:

- **Hypoperfusion Volume** (Tmax ≥6s)
- **Infarct Core Volume** (Tmax ≥10s & CBV <2.0)
- **Penumbra Volume** (Salvageable tissue)
- **Mismatch Ratio** (Treatment eligibility)
- **Advanced Metrics**: HIR, PRR, CBV Index, Collateral Grade

### ✨ Key Features

- 🚀 **One-Click Analysis**: Select folder → Analyze → View results
- 🎨 **Interactive Web Viewer**: Multi-series DICOM visualization with overlay controls
- 📊 **Apple Design UI**: Beautiful, intuitive interface following macOS design guidelines
- 🔬 **Research-Grade Metrics**: Based on validated stroke imaging papers
- 🌈 **Smart Masking**: Automatic brain tissue segmentation with background removal
- 📱 **Native macOS**: Optimized for Apple Silicon and Intel Macs

---

## 🖥️ System Requirements

### Minimum Requirements
- **OS**: macOS 10.15 (Catalina) or later
- **Python**: 3.8 or higher
- **RAM**: 8 GB
- **Storage**: 500 MB free space

### Recommended
- **OS**: macOS 13 (Ventura) or later
- **Python**: 3.10+
- **RAM**: 16 GB
- **Processor**: Apple Silicon (M1/M2/M3) or Intel Core i5+

---

## 📦 Installation

### Quick Install (5 minutes)

```bash
# 1. Clone the repository
git clone https://github.com/HyukJang1/ct-perfusion-auto.git
cd ct-perfusion-auto

# 2. Install dependencies
pip3 install -r requirements.txt

# 3. Run the application
python3 ct_perfusion_viewer.py
```

### Detailed Installation

#### Step 1: Install Python (if not already installed)

```bash
# Check Python version
python3 --version

# If Python is not installed, install via Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install python@3.10
```

#### Step 2: Create Virtual Environment (Recommended)

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### Step 3: Verify Installation

```bash
# Test import
python3 -c "import PyQt5; import pydicom; import numpy; print('✅ All dependencies installed!')"
```

---

## 🚀 Quick Start

### 1. Launch Application

```bash
python3 ct_perfusion_viewer.py
```

### 2. Select DICOM Folder

Click **"📁 Select Folder"** and choose your CT Perfusion DICOM directory.

### 3. Start Analysis

Click **"🚀 Start Analysis"** and wait for processing to complete (2-3 minutes).

### 4. View Results

- **Metrics Table**: View calculated volumes and ratios
- **Web Viewer**: Click **"🌐 View Results"** to open interactive viewer
- **Result Folder**: Click **"📂 Result Folder"** to access output files

---

## 📊 Output Files

```
analysis_results/
└── [PatientID_DateTime]/
    ├── perfusion_metrics.json      # Calculated metrics
    ├── masks.npz                    # Binary masks (hypoperfusion, core, penumbra)
    └── viewer/
        └── viewer.html              # Interactive web viewer
```

### Metrics JSON Structure

```json
{
  "patient_info": {
    "dicom_dir": "/path/to/dicom",
    "patient_name": "PatientID"
  },
  "metrics": {
    "hypoperfusion_volume_ml": 227.3,
    "infarct_core_volume_ml": 53.6,
    "penumbra_volume_ml": 173.7,
    "mismatch_ratio": 4.24,
    "hir": 0.249,
    "prr": 0.764,
    "corrected_cbv_index": 0.814,
    "collateral_grade": "Good (ASITN/SIR 3-4)"
  }
}
```

---

## 🎨 Web Viewer Features

### Interactive Controls

- **🖱️ Mouse Wheel**: Navigate through slices
- **🔘 Overlay Buttons**: Toggle hypoperfusion, core, penumbra masks
- **🎨 Color Picker**: Customize overlay colors
- **📊 Opacity Slider**: Adjust overlay transparency
- **🖼️ Thumbnails**: Quick slice navigation

### Overlay Color Scheme

| Overlay | Default Color | Clinical Meaning |
|---------|--------------|------------------|
| 🟢 Hypoperfusion | Green | Tmax ≥6s (total ischemic area) |
| 🔴 Core | Red | Tmax ≥10s & CBV <2.0 (irreversibly damaged) |
| 🟡 Penumbra | Yellow | 6s ≤ Tmax <10s (salvageable tissue) |

---

## 🔬 Clinical Interpretation

### Mismatch Ratio

```
Mismatch Ratio = Hypoperfusion Volume / Core Volume
```

- **>1.8**: ✅ Suitable for thrombectomy (large salvageable penumbra)
- **<1.8**: ⚠️ Limited benefit from reperfusion therapy

### Collateral Grade (CBV Index)

- **Good (>0.7)**: Robust collateral circulation
- **Intermediate (0.4-0.7)**: Moderate collateral support
- **Poor (<0.4)**: Insufficient collateral flow

### Hypoperfusion Intensity Ratio (HIR)

```
HIR = Core Volume (Tmax >10s) / Hypoperfusion Volume (Tmax >6s)
```

- **Low HIR (<0.4)**: Favorable penumbral pattern
- **High HIR (>0.4)**: Large core relative to hypoperfusion

---

## 🛠️ Advanced Usage

### Command-Line Analysis

```bash
# Extract metrics only
python3 scripts/extract_metrics_from_dicom.py \
  --dicom_dir /path/to/dicom \
  --output_dir /path/to/output

# Generate web viewer
python3 scripts/generate_dicom_viewer.py \
  --dicom_dir /path/to/dicom \
  --metrics /path/to/metrics.json \
  --output_dir /path/to/output
```

### Batch Processing

```python
from pathlib import Path
import subprocess

dicom_folders = Path("/path/to/patients").glob("*/")

for folder in dicom_folders:
    subprocess.run([
        "python3", "scripts/extract_metrics_from_dicom.py",
        "--dicom_dir", str(folder),
        "--output_dir", f"results/{folder.name}"
    ])
```

---

## 🐛 Troubleshooting

### Issue: "Module not found" error

**Solution**: Ensure all dependencies are installed
```bash
pip3 install -r requirements.txt
```

### Issue: "No TMAXD series found"

**Solution**: Verify your DICOM folder contains Siemens CT Perfusion data with TMAXD series

### Issue: Web viewer shows blank overlays

**Solution**: Delete `analysis_results` folder and re-run analysis
```bash
rm -rf analysis_results/[PatientID]
```

### Issue: Font warnings on startup

**Solution**: These are harmless PyQt5 warnings and can be ignored
```
qt.qpa.fonts: Populating font family aliases took 50 ms
```

---

## 📚 Technical Details

### RGB to Scalar Conversion

Siemens CT Perfusion stores parametric maps as RGB images. NeuroFlow implements the reverse mapping:

```python
# Time series (Tmax, MTT, TTP)
scalar = rgb_to_scalar_siemens_time(r, g, b)

# Flow/Volume series (CBF, CBV)
scalar = rgb_to_scalar_siemens_flow(r, g, b)
```

**Background Removal**: Pixels with `RGB sum <10` are set to 0 to exclude non-brain tissue.

### Brain Mask Generation

```python
brain_mask = (tmax_volume > 0.1) | (cbv_volume > 0.5) | (cbf_volume > 0.5)
```

This ensures only brain parenchyma is included in perfusion calculations.

### Mask Definitions

```python
# Hypoperfusion: Tmax ≥6s within brain
hypoperfusion_mask = brain_mask & (tmax >= 6.0)

# Core: Tmax ≥10s & CBV <2.0 within brain
core_mask = brain_mask & (tmax >= 10.0) & (cbv < 2.0)

# Penumbra: Hypoperfusion - Core
penumbra_mask = hypoperfusion_mask & (~core_mask)
```

---

## 🎯 Validation

NeuroFlow has been validated against:
- ✅ Siemens syngo.via CT Perfusion
- ✅ Manual ROI measurements by neuroradiologists
- ✅ Published stroke imaging papers

See [VALIDATION.md](VALIDATION.md) for detailed validation results.

---

## 📖 References

1. **Mismatch Ratio**: Campbell et al. (2012) - EXTEND-IA trial
2. **CBV Index**: Menon et al. (2015) - ESCAPE trial  
3. **HIR**: Olivot et al. (2014) - DEFUSE 2 trial
4. **RGB Conversion**: [neurolabusc/rgb2scalar](https://github.com/neurolabusc/rgb2scalar)

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

---

## 👨‍⚕️ Author

**Hyuk Jang**
- GitHub: [@HyukJang1](https://github.com/HyukJang1)
- Project: [ct-perfusion-auto](https://github.com/HyukJang1/ct-perfusion-auto)

---

## 🙏 Acknowledgments

- Siemens Healthineers for CT Perfusion technology
- Chris Rorden for RGB to scalar conversion algorithms
- PyQt5 and Python medical imaging community

---

## 📞 Support

For issues, questions, or feature requests:
- 🐛 [Open an Issue](https://github.com/HyukJang1/ct-perfusion-auto/issues)
- 💬 [Discussions](https://github.com/HyukJang1/ct-perfusion-auto/discussions)

---

**⚕️ For Research Use Only - Not for Clinical Diagnosis**
