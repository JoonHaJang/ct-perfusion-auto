#!/usr/bin/env python3
"""
Convert DICOM series to NIfTI format for CT perfusion analysis.

Supports:
- Single DICOM series → single NIfTI
- Multiple series in directory → multiple NIfTI files
- Automatic series detection and grouping
"""
import argparse
import os
import json
from pathlib import Path
import numpy as np
import pydicom
from collections import defaultdict
import nibabel as nib


def rgb_to_scalar_siemens(rgb_array, series_description=""):
    """
    Convert Siemens CT Perfusion RGB to scalar values
    Based on: https://github.com/neurolabusc/rgb2scalar
    
    Args:
        rgb_array: RGB pixel array (H, W, 3)
        series_description: Series description to determine max value
        
    Returns:
        Scalar array with actual perfusion values
    """
    r = rgb_array[:, :, 0].astype(float)
    g = rgb_array[:, :, 1].astype(float)
    b = rgb_array[:, :, 2].astype(float)
    
    # RGB를 intensity로 변환
    intensity = 0.299 * r + 0.587 * g + 0.114 * b
    
    # Series에 따라 최대값 결정
    max_value = 12.0  # Default for Tmax
    if "CBV" in series_description.upper():
        max_value = 100.0  # CBV range 0-100
    elif "CBF" in series_description.upper():
        max_value = 100.0  # CBF range 0-100
    elif "MTT" in series_description.upper() or "TTD" in series_description.upper():
        max_value = 15.0   # MTT/TTD range 0-15
    elif "TMAX" in series_description.upper():
        max_value = 12.0   # Tmax range 0-12
    
    # 0-max_value 범위로 스케일링
    scalar_value = (intensity / 255.0) * max_value
    
    return scalar_value


def read_dicom_series(dicom_dir, series_uid=None, convert_rgb=True):
    """Read DICOM series from directory.
    
    Args:
        dicom_dir: Directory containing DICOM files
        series_uid: Optional specific SeriesInstanceUID to load
        convert_rgb: If True, convert RGB images to scalar values (Siemens CT Perfusion)
        
    Returns:
        tuple: (volume_data, affine_matrix, metadata_dict)
    """
    dicom_files = []
    
    # Collect all DICOM files
    for root, dirs, files in os.walk(dicom_dir):
        for fname in files:
            if fname.endswith('.dcm') or fname.startswith('EXPORT_'):
                fpath = os.path.join(root, fname)
                try:
                    ds = pydicom.dcmread(fpath, stop_before_pixels=True)
                    if series_uid is None or ds.SeriesInstanceUID == series_uid:
                        dicom_files.append((fpath, ds))
                except Exception:
                    continue
    
    if not dicom_files:
        raise ValueError(f"No valid DICOM files found in {dicom_dir}")
    
    # Sort by InstanceNumber or SliceLocation
    def sort_key(item):
        ds = item[1]
        if hasattr(ds, 'InstanceNumber'):
            return ds.InstanceNumber
        elif hasattr(ds, 'SliceLocation'):
            return ds.SliceLocation
        return 0
    
    dicom_files.sort(key=sort_key)
    
    # Get series description for RGB conversion
    first_ds_temp = pydicom.dcmread(dicom_files[0][0])
    series_description = getattr(first_ds_temp, 'SeriesDescription', '')
    
    # Check if this is Siemens CT Perfusion RGB (print once)
    is_siemens_perfusion = False
    if convert_rgb:
        test_pixel = first_ds_temp.pixel_array
        if len(test_pixel.shape) == 3 and test_pixel.shape[-1] == 3:
            if "RGB" in series_description or "Perfusion" in series_description:
                is_siemens_perfusion = True
                print(f"Converting Siemens CT Perfusion RGB to scalar ({series_description})")
    
    # Read pixel data
    slices = []
    for fpath, _ in dicom_files:
        ds = pydicom.dcmread(fpath)
        pixel_array = ds.pixel_array
        
        # Convert RGB to scalar values for Siemens CT Perfusion
        if convert_rgb and len(pixel_array.shape) == 3 and pixel_array.shape[-1] == 3:
            if is_siemens_perfusion:
                pixel_array = rgb_to_scalar_siemens(pixel_array, series_description)
            else:
                # Standard RGB to grayscale
                pixel_array = (0.299 * pixel_array[..., 0] + 
                              0.587 * pixel_array[..., 1] + 
                              0.114 * pixel_array[..., 2]).astype(pixel_array.dtype)
        
        slices.append(pixel_array)
    
    # Stack into 3D volume
    volume = np.stack(slices, axis=0)
    
    # Get first slice for metadata
    first_ds = pydicom.dcmread(dicom_files[0][0])
    
    # Build affine matrix
    affine = build_affine_matrix(first_ds, len(slices))
    
    # Extract metadata
    metadata = {
        "SeriesDescription": getattr(first_ds, 'SeriesDescription', 'Unknown'),
        "SeriesNumber": getattr(first_ds, 'SeriesNumber', 0),
        "SeriesInstanceUID": getattr(first_ds, 'SeriesInstanceUID', ''),
        "Modality": getattr(first_ds, 'Modality', 'CT'),
        "SliceCount": len(slices),
        "ImageShape": list(volume.shape)
    }
    
    return volume, affine, metadata


def build_affine_matrix(dicom_dataset, num_slices):
    """Build NIfTI affine matrix from DICOM metadata.
    
    Args:
        dicom_dataset: pydicom Dataset object
        num_slices: Number of slices in volume
        
    Returns:
        4x4 affine transformation matrix
    """
    # Get pixel spacing
    if hasattr(dicom_dataset, 'PixelSpacing'):
        pixel_spacing = dicom_dataset.PixelSpacing
        dx, dy = float(pixel_spacing[1]), float(pixel_spacing[0])
    else:
        dx, dy = 1.0, 1.0
    
    # Get slice thickness
    if hasattr(dicom_dataset, 'SliceThickness'):
        dz = float(dicom_dataset.SliceThickness)
    elif hasattr(dicom_dataset, 'SpacingBetweenSlices'):
        dz = float(dicom_dataset.SpacingBetweenSlices)
    else:
        dz = 1.0
    
    # Get image position (origin)
    if hasattr(dicom_dataset, 'ImagePositionPatient'):
        origin = [float(x) for x in dicom_dataset.ImagePositionPatient]
    else:
        origin = [0.0, 0.0, 0.0]
    
    # Get image orientation
    if hasattr(dicom_dataset, 'ImageOrientationPatient'):
        orientation = [float(x) for x in dicom_dataset.ImageOrientationPatient]
        row_cosine = np.array(orientation[:3])
        col_cosine = np.array(orientation[3:6])
        slice_cosine = np.cross(row_cosine, col_cosine)
    else:
        # Default to identity orientation
        row_cosine = np.array([1, 0, 0])
        col_cosine = np.array([0, 1, 0])
        slice_cosine = np.array([0, 0, 1])
    
    # Build affine matrix
    affine = np.eye(4)
    affine[0, 0] = row_cosine[0] * dx
    affine[1, 0] = row_cosine[1] * dx
    affine[2, 0] = row_cosine[2] * dx
    affine[0, 1] = col_cosine[0] * dy
    affine[1, 1] = col_cosine[1] * dy
    affine[2, 1] = col_cosine[2] * dy
    affine[0, 2] = slice_cosine[0] * dz
    affine[1, 2] = slice_cosine[1] * dz
    affine[2, 2] = slice_cosine[2] * dz
    affine[0, 3] = origin[0]
    affine[1, 3] = origin[1]
    affine[2, 3] = origin[2]
    
    return affine


def detect_series(dicom_dir):
    """Detect all DICOM series in directory.
    
    Args:
        dicom_dir: Directory to scan
        
    Returns:
        dict: {SeriesInstanceUID: {description, count, files}}
    """
    series_info = defaultdict(lambda: {"files": [], "description": "", "number": 0})
    
    for root, dirs, files in os.walk(dicom_dir):
        for fname in files:
            if fname.endswith('.dcm') or fname.startswith('EXPORT_'):
                fpath = os.path.join(root, fname)
                try:
                    ds = pydicom.dcmread(fpath, stop_before_pixels=True)
                    uid = ds.SeriesInstanceUID
                    series_info[uid]["files"].append(fpath)
                    series_info[uid]["description"] = getattr(ds, 'SeriesDescription', 'Unknown')
                    series_info[uid]["number"] = getattr(ds, 'SeriesNumber', 0)
                except Exception:
                    continue
    
    # Convert to regular dict with counts
    result = {}
    for uid, info in series_info.items():
        result[uid] = {
            "description": info["description"],
            "series_number": info["number"],
            "file_count": len(info["files"])
        }
    
    return result


def convert_dicom_to_nifti(dicom_dir, output_path, series_uid=None, convert_rgb=True):
    """Convert DICOM series to NIfTI file.
    
    Args:
        dicom_dir: Directory containing DICOM files
        output_path: Output NIfTI file path (.nii.gz)
        series_uid: Optional specific series to convert
        convert_rgb: If True, convert RGB images to grayscale
        
    Returns:
        dict: Conversion metadata
    """
    volume, affine, metadata = read_dicom_series(dicom_dir, series_uid, convert_rgb)
    
    # Create NIfTI image
    nifti_img = nib.Nifti1Image(volume, affine)
    
    # Save
    nib.save(nifti_img, output_path)
    
    result = {
        "input_dir": str(dicom_dir),
        "output_file": str(output_path),
        "volume_shape": list(volume.shape),
        "metadata": metadata
    }
    
    return result


def main():
    ap = argparse.ArgumentParser(description="Convert DICOM series to NIfTI format")
    ap.add_argument("--input", required=True, help="Input DICOM directory")
    ap.add_argument("--output", help="Output NIfTI file path (.nii.gz)")
    ap.add_argument("--detect", action="store_true", help="Detect and list all series")
    ap.add_argument("--series_uid", help="Specific SeriesInstanceUID to convert")
    ap.add_argument("--series_desc", help="Series description keyword to match")
    ap.add_argument("--output_dir", help="Output directory for batch conversion")
    ap.add_argument("--batch", action="store_true", help="Convert all series in directory")
    ap.add_argument("--keep_rgb", action="store_true", help="Keep RGB channels (default: convert to grayscale)")
    args = ap.parse_args()
    
    input_dir = Path(args.input)
    
    if not input_dir.exists():
        print(f"Error: Input directory not found: {input_dir}")
        return
    
    # Detect series mode
    if args.detect:
        series_dict = detect_series(input_dir)
        print(json.dumps(series_dict, indent=2, ensure_ascii=False))
        return
    
    # Batch conversion mode
    if args.batch:
        if not args.output_dir:
            print("Error: --output_dir required for batch conversion")
            return
        
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        series_dict = detect_series(input_dir)
        results = []
        
        for uid, info in series_dict.items():
            desc = info["description"].replace(" ", "_").replace("/", "-")
            series_num = info["series_number"]
            output_name = f"series_{series_num:03d}_{desc}.nii.gz"
            output_path = output_dir / output_name
            
            try:
                result = convert_dicom_to_nifti(input_dir, output_path, uid, convert_rgb=not args.keep_rgb)
                results.append(result)
                print(f"[OK] Converted: {output_name}")
            except Exception as e:
                print(f"[FAIL] Failed {output_name}: {e}")
        
        # Save summary
        summary_path = output_dir / "conversion_summary.json"
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\nBatch conversion complete: {len(results)} series")
        print(f"Summary saved to: {summary_path}")
        return
    
    # Single conversion mode
    if not args.output:
        print("Error: --output required for single conversion")
        return
    
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Filter by series description if provided
    series_uid = args.series_uid
    if args.series_desc and not series_uid:
        series_dict = detect_series(input_dir)
        for uid, info in series_dict.items():
            if args.series_desc.lower() in info["description"].lower():
                series_uid = uid
                print(f"Matched series: {info['description']} (UID: {uid})")
                break
        
        if not series_uid:
            print(f"Error: No series found matching '{args.series_desc}'")
            return
    
    try:
        result = convert_dicom_to_nifti(input_dir, output_path, series_uid, convert_rgb=not args.keep_rgb)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Error during conversion: {e}")
        raise


if __name__ == "__main__":
    main()
