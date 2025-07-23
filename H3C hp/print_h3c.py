import pandas as pd
import os

# === Path to Excel file ===
EXCEL_PATH = r"Device-list.xlsx"  # <-- Adjust if needed
OUTPUT_EXCEL = "h3c_switches_filtered.xlsx"      

# === Load Excel ===
df = pd.read_excel(EXCEL_PATH)

# === Normalize column names ===
df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]

# === Identify required columns ===
device_col = next((c for c in df.columns if "device_type" in c or "device" in c), None)
hostname_col = next((c for c in df.columns if "host" in c), None)
ip_col = next((c for c in df.columns if "ip" in c), None)
model_col = next((c for c in df.columns if "model" in c), None)

# === Filter H3C Switches ===
h3c_df = df[df[device_col].str.lower() == "h3c switch"]

# === Show results ===
filtered = h3c_df[[device_col, hostname_col, ip_col, model_col]]
print(filtered)
print(f"\nTotal H3C Switches found: {len(filtered)}")

# === Save to Excel ===
filtered.to_excel(OUTPUT_EXCEL, index=False)
print(f"[INFO] Filtered H3C switch info saved to: {os.path.abspath(OUTPUT_EXCEL)}")
