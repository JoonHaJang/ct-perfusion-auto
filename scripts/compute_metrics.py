#!/usr/bin/env python3
"""
Compute CT perfusion metrics from Tmax, CBV, rCBF maps.

Calculated metrics:
- Hypoperfusion (Tmax > 6s)
- Infarct Core (rCBF < 30% ∩ Tmax > 6s)
- Penumbra (Hypoperfusion - Infarct Core)
- Mismatch Ratio (Hypoperfusion / Infarct Core)
- PRR (Penumbra Rescue Rate %)
- Corrected/Conventional CBV Index
- HIR (Hypoperfusion Intensity Ratio)
- PVT (Prolonged Venous Transit)
"""
import argparse
import json
import os
import numpy as np
import pandas as pd
from ctperf.io.loaders import load_nifti, save_nifti_like


def compute_hypoperfusion(tmax_data, threshold=6.0):
    """Compute hypoperfusion mask (Tmax > threshold seconds).
    
    Args:
        tmax_data: 3D numpy array of Tmax values
        threshold: Tmax threshold in seconds (default 6.0)
        
    Returns:
        Binary mask (1 where Tmax > threshold)
    """
    return (tmax_data > threshold).astype(np.uint8)


def compute_infarct_core(rcbf_data, tmax_data, rcbf_threshold=0.3, tmax_threshold=6.0, roi_contra=None):
    """Compute infarct core mask (rCBF < 30% of contralateral ∩ Tmax > 6s).
    
    Args:
        rcbf_data: 3D numpy array of rCBF values
        tmax_data: 3D numpy array of Tmax values
        rcbf_threshold: Relative CBF threshold (default 0.3 = 30%)
        tmax_threshold: Tmax threshold in seconds (default 6.0)
        roi_contra: Optional contralateral ROI mask for normalization
        
    Returns:
        Binary mask (1 where criteria met)
    """
    if roi_contra is not None:
        # Normalize rCBF by contralateral mean
        contra_mean = rcbf_data[roi_contra > 0].mean()
        if contra_mean > 0:
            rcbf_normalized = rcbf_data / contra_mean
        else:
            rcbf_normalized = rcbf_data
    else:
        # Use absolute rCBF values
        rcbf_normalized = rcbf_data
    
    core_mask = (rcbf_normalized < rcbf_threshold) & (tmax_data > tmax_threshold)
    return core_mask.astype(np.uint8)


def compute_penumbra(hypoperfusion_mask, core_mask):
    """Compute penumbra (Hypoperfusion - Infarct Core).
    
    Args:
        hypoperfusion_mask: Binary mask of hypoperfusion region
        core_mask: Binary mask of infarct core
        
    Returns:
        Binary mask of penumbra region
    """
    penumbra = (hypoperfusion_mask > 0) & (core_mask == 0)
    return penumbra.astype(np.uint8)


def compute_mismatch_ratio(hypoperfusion_volume, core_volume):
    """Compute mismatch ratio (Hypoperfusion / Core).
    
    Args:
        hypoperfusion_volume: Volume in voxels or mL
        core_volume: Volume in voxels or mL
        
    Returns:
        Mismatch ratio (float), or None if core is zero
    """
    if core_volume > 0:
        return hypoperfusion_volume / core_volume
    return None


def compute_prr(penumbra_volume, hypoperfusion_volume):
    """Compute Penumbra Rescue Rate (PRR %).
    
    Args:
        penumbra_volume: Penumbra volume
        hypoperfusion_volume: Total hypoperfusion volume
        
    Returns:
        PRR as percentage (0-100)
    """
    if hypoperfusion_volume > 0:
        return (penumbra_volume / hypoperfusion_volume) * 100
    return 0.0


def compute_cbv_index(cbv_data, core_mask, hypoperfusion_mask, method="corrected"):
    """Compute CBV index (mean CBV in core / mean CBV in hypoperfusion).
    
    Args:
        cbv_data: 3D numpy array of CBV values
        core_mask: Binary mask of infarct core
        hypoperfusion_mask: Binary mask of hypoperfusion
        method: "corrected" or "conventional"
        
    Returns:
        CBV index (float)
    """
    core_cbv = cbv_data[core_mask > 0]
    hypo_cbv = cbv_data[hypoperfusion_mask > 0]
    
    if len(core_cbv) > 0 and len(hypo_cbv) > 0:
        if method == "corrected":
            # Corrected: exclude core from hypoperfusion
            penumbra_mask = (hypoperfusion_mask > 0) & (core_mask == 0)
            penumbra_cbv = cbv_data[penumbra_mask]
            if len(penumbra_cbv) > 0:
                return core_cbv.mean() / penumbra_cbv.mean()
        else:
            # Conventional: use all hypoperfusion
            return core_cbv.mean() / hypo_cbv.mean()
    
    return None


def compute_hir(tmax_data, hypoperfusion_mask, severe_threshold=10.0, mild_threshold=6.0):
    """Compute Hypoperfusion Intensity Ratio (HIR).
    
    HIR = Volume(Tmax > 10s) / Volume(Tmax > 6s)
    
    Args:
        tmax_data: 3D numpy array of Tmax values
        hypoperfusion_mask: Binary mask of hypoperfusion (Tmax > 6s)
        severe_threshold: Severe delay threshold (default 10s)
        mild_threshold: Mild delay threshold (default 6s)
        
    Returns:
        HIR ratio (0-1)
    """
    severe_volume = (tmax_data > severe_threshold).sum()
    mild_volume = (tmax_data > mild_threshold).sum()
    
    if mild_volume > 0:
        return severe_volume / mild_volume
    return 0.0


def compute_pvt(vof_csv, aif_csv, threshold_ratio=1.5):
    """Compute Prolonged Venous Transit (PVT) from VOF/AIF curves.
    
    Args:
        vof_csv: Path to VOF CSV (time_sec, vof)
        aif_csv: Path to AIF CSV (time_sec, aif)
        threshold_ratio: Ratio threshold for prolonged transit
        
    Returns:
        dict with PVT metrics
    """
    try:
        vof_df = pd.read_csv(vof_csv)
        aif_df = pd.read_csv(aif_csv)
        
        # Find time to peak
        vof_ttp = vof_df.loc[vof_df.iloc[:, 1].idxmax(), vof_df.columns[0]]
        aif_ttp = aif_df.loc[aif_df.iloc[:, 1].idxmax(), aif_df.columns[0]]
        
        transit_time = vof_ttp - aif_ttp
        is_prolonged = transit_time > threshold_ratio
        
        return {
            "vof_ttp": float(vof_ttp),
            "aif_ttp": float(aif_ttp),
            "transit_time": float(transit_time),
            "is_prolonged": bool(is_prolonged)
        }
    except Exception as e:
        return {"error": str(e)}


def main():
    ap = argparse.ArgumentParser(description="Compute CT perfusion metrics")
    ap.add_argument("--tmax", required=True, help="Tmax NIfTI file")
    ap.add_argument("--roi_contra", help="Contralateral ROI mask NIfTI")
    ap.add_argument("--cbv", help="CBV NIfTI file")
    ap.add_argument("--rcbf", help="rCBF NIfTI file")
    ap.add_argument("--vof_csv", help="VOF time curve CSV")
    ap.add_argument("--aif_csv", help="AIF time curve CSV")
    ap.add_argument("--out_dir", default="outputs", help="Output directory")
    ap.add_argument("--save_masks", action="store_true", help="Save intermediate masks")
    ap.add_argument("--tmax_threshold", type=float, default=6.0, help="Tmax threshold (seconds)")
    ap.add_argument("--rcbf_threshold", type=float, default=0.3, help="rCBF threshold (fraction)")
    args = ap.parse_args()
    
    os.makedirs(args.out_dir, exist_ok=True)
    
    # Load data
    tmax_data, tmax_img = load_nifti(args.tmax)
    
    roi_contra_data = None
    if args.roi_contra:
        roi_contra_data, _ = load_nifti(args.roi_contra)
    
    # Compute hypoperfusion
    hypo_mask = compute_hypoperfusion(tmax_data, args.tmax_threshold)
    hypo_volume = hypo_mask.sum()
    
    results = {
        "hypoperfusion_volume_voxels": int(hypo_volume),
        "tmax_threshold": args.tmax_threshold
    }
    
    if args.save_masks:
        save_nifti_like(tmax_img, hypo_mask, os.path.join(args.out_dir, "hypoperfusion_mask.nii.gz"))
    
    # Compute infarct core if rCBF available
    if args.rcbf:
        rcbf_data, rcbf_img = load_nifti(args.rcbf)
        core_mask = compute_infarct_core(rcbf_data, tmax_data, args.rcbf_threshold, 
                                         args.tmax_threshold, roi_contra_data)
        core_volume = core_mask.sum()
        
        # Penumbra
        penumbra_mask = compute_penumbra(hypo_mask, core_mask)
        penumbra_volume = penumbra_mask.sum()
        
        # Mismatch ratio
        mismatch = compute_mismatch_ratio(hypo_volume, core_volume)
        
        # PRR
        prr = compute_prr(penumbra_volume, hypo_volume)
        
        results.update({
            "infarct_core_volume_voxels": int(core_volume),
            "penumbra_volume_voxels": int(penumbra_volume),
            "mismatch_ratio": float(mismatch) if mismatch else None,
            "prr_percent": float(prr),
            "rcbf_threshold": args.rcbf_threshold
        })
        
        if args.save_masks:
            save_nifti_like(tmax_img, core_mask, os.path.join(args.out_dir, "infarct_core_mask.nii.gz"))
            save_nifti_like(tmax_img, penumbra_mask, os.path.join(args.out_dir, "penumbra_mask.nii.gz"))
    
    # CBV index if CBV available
    if args.cbv and args.rcbf:
        cbv_data, _ = load_nifti(args.cbv)
        cbv_corrected = compute_cbv_index(cbv_data, core_mask, hypo_mask, "corrected")
        cbv_conventional = compute_cbv_index(cbv_data, core_mask, hypo_mask, "conventional")
        
        results.update({
            "cbv_index_corrected": float(cbv_corrected) if cbv_corrected else None,
            "cbv_index_conventional": float(cbv_conventional) if cbv_conventional else None
        })
    
    # HIR
    hir = compute_hir(tmax_data, hypo_mask)
    results["hir"] = float(hir)
    
    # PVT if VOF/AIF available
    if args.vof_csv and args.aif_csv:
        pvt_results = compute_pvt(args.vof_csv, args.aif_csv)
        results["pvt"] = pvt_results
    
    # Save results
    output_json = os.path.join(args.out_dir, "metrics.json")
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
