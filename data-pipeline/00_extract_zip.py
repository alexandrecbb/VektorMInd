import zipfile
import os
import shutil

zip_path = "data-pipeline/Fake-Sample-Data.zip"
out_dir = "data/03_primary"

os.makedirs(out_dir, exist_ok=True)

with zipfile.ZipFile(zip_path, 'r') as z:
    for file_info in z.infolist():
        if ("filing_data.parquet" in file_info.filename or "TSLA_fake.csv" in file_info.filename) and not file_info.filename.startswith("__MACOSX"):
            print("Found file:", file_info.filename)
            # Extract it directly to the primary directory
            filename = os.path.basename(file_info.filename)
            target_dir = "data/temp" if "TSLA_fake.csv" in filename else out_dir
            os.makedirs(target_dir, exist_ok=True)
            with z.open(file_info) as source, open(os.path.join(target_dir, filename), "wb") as target:
                shutil.copyfileobj(source, target)
            print(f"Extracted to {os.path.join(out_dir, filename)}")
