@echo off
cd /d "c:\Users\USER\Desktop\의료 저널\ct-perfusion-auto"
python scripts\generate_dicom_viewer.py --dicom_dir "C:\Users\USER\Desktop\의료 저널\Research\CTP_MT\487460_안연순_20240423225748" --metrics "analysis_results\487460_안연순_20240423225748\perfusion_metrics.json" --output_dir "analysis_results\487460_안연순_20240423225748\viewer_new"
pause
