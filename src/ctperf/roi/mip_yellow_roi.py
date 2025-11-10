import numpy as np
from PIL import Image

def yellow_mask_from_mip_png(png_path, hsv_low=(20, 80, 80), hsv_high=(60, 255, 255)):
    """Extract yellow ROI from a MIP PNG/JPG by HSV threshold.
    Returns a 2D uint8 mask with 1 for yellow pixels.
    hsv_low/high use OpenCV-style ranges: H:0-179, S:0-255, V:0-255.
    """
    img = Image.open(png_path).convert("RGB")
    arr = np.array(img).astype(np.uint8)
    r, g, b = arr[...,0]/255.0, arr[...,1]/255.0, arr[...,2]/255.0
    cmax = np.maximum(np.maximum(r,g), b)
    cmin = np.minimum(np.minimum(r,g), b)
    delta = cmax - cmin + 1e-12
    h = np.zeros_like(cmax)
    mask = (delta != 0)
    rmask = (cmax == r) & mask
    gmask = (cmax == g) & mask
    bmask = (cmax == b) & mask
    h[rmask] = (60 * (((g - b)/delta) % 6))[rmask]
    h[gmask] = (60 * (((b - r)/delta) + 2))[gmask]
    h[bmask] = (60 * (((r - g)/delta) + 4))[bmask]
    s = np.zeros_like(cmax)
    s[cmax != 0] = (delta / cmax)[cmax != 0]
    v = cmax
    H = (h / 2).astype(np.uint8)
    S = (s * 255).astype(np.uint8)
    V = (v * 255).astype(np.uint8)
    hsv = np.stack([H,S,V], axis=-1)
    lo = np.array(hsv_low, dtype=np.uint8)
    hi = np.array(hsv_high, dtype=np.uint8)
    return ((hsv >= lo) & (hsv <= hi)).all(axis=-1).astype(np.uint8)

def mip_mask_to_3d(mask_2d, ref_shape, axis="z"):
    z,y,x = ref_shape
    if axis == "z":
        if mask_2d.shape != (y,x):
            raise ValueError(f"mask shape {mask_2d.shape} must match (Y,X)=({y},{x}) for axis 'z'")
        vol = np.repeat(mask_2d[None,...], z, axis=0)
    elif axis == "y":
        if mask_2d.shape != (z,x):
            raise ValueError(f"mask shape {mask_2d.shape} must match (Z,X)=({z},{x}) for axis 'y'")
        vol = np.repeat(mask_2d[:,None,:], y, axis=1)
    elif axis == "x":
        if mask_2d.shape != (z,y):
            raise ValueError(f"mask shape {mask_2d.shape} must match (Z,Y)=({z},{y}) for axis 'x'")
        vol = np.repeat(mask_2d[:,:,None], x, axis=2)
    else:
        raise ValueError("axis must be one of 'z','y','x'")
    return vol.astype(np.uint8)
