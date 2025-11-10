"""Setup script for ct-perfusion-auto package."""
from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

setup(
    name="ct-perfusion-auto",
    version="0.1.0",
    author="Medical Research Team",
    description="Automated CT perfusion analysis for stroke assessment",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/ct-perfusion-auto",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.8",
    install_requires=[
        "numpy>=1.21.0",
        "nibabel>=3.2.0",
        "Pillow>=9.0.0",
        "pandas>=1.3.0",
        "pydicom>=2.3.0",
    ],
    entry_points={
        "console_scripts": [
            "ctp-convert=scripts.convert_dicom_to_nifti:main",
            "ctp-metrics=scripts.compute_metrics:main",
            "ctp-roi=scripts.analyze_mip_image:main",
            "ctp-batch=scripts.batch_process_patients:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Healthcare Industry",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Medical Science Apps.",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    keywords="medical-imaging ct-perfusion stroke neuroimaging dicom nifti",
)
