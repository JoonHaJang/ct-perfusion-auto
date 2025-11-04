#!/usr/bin/env python3
"""
DICOM 파일 상세 분석 - RGB vs 원본 데이터 확인
"""
import pydicom
from pathlib import Path
import numpy as np


def inspect_dicom_file(dcm_path):
    """DICOM 파일 상세 분석"""
    ds = pydicom.dcmread(dcm_path)
    
    print("="*60)
    print(f"DICOM File: {dcm_path.name}")
    print("="*60)
    
    # 기본 정보
    print("\n📋 Basic Information:")
    print(f"  Patient Name: {ds.get('PatientName', 'N/A')}")
    print(f"  Study Date: {ds.get('StudyDate', 'N/A')}")
    print(f"  Series Description: {ds.get('SeriesDescription', 'N/A')}")
    print(f"  Modality: {ds.get('Modality', 'N/A')}")
    
    # 이미지 정보
    print("\n🖼️  Image Information:")
    print(f"  Image Type: {ds.get('ImageType', 'N/A')}")
    print(f"  Photometric Interpretation: {ds.get('PhotometricInterpretation', 'N/A')}")
    print(f"  Samples Per Pixel: {ds.get('SamplesPerPixel', 'N/A')}")
    print(f"  Rows x Columns: {ds.Rows} x {ds.Columns}")
    print(f"  Bits Allocated: {ds.get('BitsAllocated', 'N/A')}")
    print(f"  Bits Stored: {ds.get('BitsStored', 'N/A')}")
    
    # 픽셀 데이터
    pixel_array = ds.pixel_array
    print(f"\n📊 Pixel Data:")
    print(f"  Shape: {pixel_array.shape}")
    print(f"  Dtype: {pixel_array.dtype}")
    print(f"  Range: [{pixel_array.min()}, {pixel_array.max()}]")
    print(f"  Mean: {pixel_array.mean():.2f}")
    
    # RGB인 경우 채널별 분석
    if len(pixel_array.shape) == 3:
        print(f"\n🎨 RGB Channels:")
        for i, color in enumerate(['R', 'G', 'B']):
            channel = pixel_array[:, :, i]
            print(f"  {color} channel: [{channel.min()}, {channel.max()}], Mean: {channel.mean():.2f}")
    
    # Rescale 정보
    print(f"\n🔢 Rescale Information:")
    print(f"  Rescale Slope: {ds.get('RescaleSlope', 'N/A')}")
    print(f"  Rescale Intercept: {ds.get('RescaleIntercept', 'N/A')}")
    
    # Window/Level
    print(f"\n🪟 Window/Level:")
    print(f"  Window Center: {ds.get('WindowCenter', 'N/A')}")
    print(f"  Window Width: {ds.get('WindowWidth', 'N/A')}")
    
    # Private tags (제조사 고유 데이터)
    print(f"\n🔐 Private Tags:")
    for elem in ds:
        if elem.tag.is_private:
            print(f"  {elem.tag}: {elem.name} = {elem.value}")
    
    return ds


def compare_all_series(dicom_dir):
    """모든 시리즈 비교"""
    dicom_files = sorted(list(Path(dicom_dir).glob("*.dcm")))
    
    # 시리즈별로 그룹화
    series_dict = {}
    for dcm_file in dicom_files:
        ds = pydicom.dcmread(dcm_file)
        series_desc = ds.get('SeriesDescription', 'Unknown')
        
        if series_desc not in series_dict:
            series_dict[series_desc] = []
        series_dict[series_desc].append(dcm_file)
    
    print("\n" + "="*60)
    print("ALL SERIES SUMMARY")
    print("="*60)
    
    for series_desc, files in series_dict.items():
        print(f"\n📁 {series_desc}")
        print(f"   Files: {len(files)}")
        
        # 첫 번째 파일 분석
        ds = pydicom.dcmread(files[0])
        pixel_array = ds.pixel_array
        
        print(f"   Shape: {pixel_array.shape}")
        print(f"   Type: {ds.get('PhotometricInterpretation', 'N/A')}")
        print(f"   Range: [{pixel_array.min()}, {pixel_array.max()}]")
        
        # RGB 여부
        if len(pixel_array.shape) == 3:
            print(f"   ⚠️  RGB Image (시각화된 이미지)")
        else:
            print(f"   ✅ Grayscale (원본 데이터 가능성)")


def main():
    dicom_dir = Path(r"C:\Users\USER\Desktop\의료 저널\Research\CTP_MT\487460_안연순_20240423225748")
    
    # 모든 시리즈 요약
    compare_all_series(dicom_dir)
    
    # TMAXD 파일 상세 분석
    print("\n\n" + "="*60)
    print("DETAILED ANALYSIS - TMAXD")
    print("="*60)
    
    tmaxd_files = []
    for dcm_file in dicom_dir.glob("*.dcm"):
        ds = pydicom.dcmread(dcm_file)
        if "TMAXD" in ds.get('SeriesDescription', ''):
            tmaxd_files.append(dcm_file)
    
    if tmaxd_files:
        # 중간 슬라이스 분석
        mid_file = sorted(tmaxd_files)[len(tmaxd_files)//2]
        inspect_dicom_file(mid_file)
    else:
        print("TMAXD 파일을 찾을 수 없습니다.")


if __name__ == "__main__":
    main()
