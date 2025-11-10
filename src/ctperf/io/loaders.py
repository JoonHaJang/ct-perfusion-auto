"""NIfTI file I/O utilities for CT perfusion analysis."""
import numpy as np
import nibabel as nib


def load_nifti(filepath):
    """Load NIfTI file and return data array and image object.
    
    Args:
        filepath: Path to .nii or .nii.gz file
        
    Returns:
        tuple: (data_array, nifti_image)
            - data_array: numpy array with image data
            - nifti_image: nibabel Nifti1Image object
    """
    img = nib.load(filepath)
    data = img.get_fdata()
    return data, img


def save_nifti_like(reference_img, data, output_path):
    """Save data as NIfTI using reference image's affine and header.
    
    Args:
        reference_img: nibabel Nifti1Image to copy affine/header from
        data: numpy array to save
        output_path: Output file path (.nii.gz)
    """
    new_img = nib.Nifti1Image(data, reference_img.affine, reference_img.header)
    nib.save(new_img, output_path)


def save_nifti(data, affine, output_path, header=None):
    """Save data as NIfTI with specified affine matrix.
    
    Args:
        data: numpy array to save
        affine: 4x4 affine transformation matrix
        output_path: Output file path (.nii.gz)
        header: Optional nibabel header object
    """
    img = nib.Nifti1Image(data, affine, header)
    nib.save(img, output_path)
