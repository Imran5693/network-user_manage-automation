import pandas as pd
from netmiko import ConnectHandler
from getpass import getpass
from datetime import datetime
import time
import os

# === CONFIGURATION ===
EXCEL_PATH = r"h3c_switches_filtered.xlsx"   # <- Path to your Excel file
LOG_DIR = "hp_procurve_user_creation_logs"
os.makedirs(LOG_DIR, exist_ok=True)

# === USER INPUT ===
USERNAME = input("Enter the username to create: ")
USER_PASS = getpass(f"Enter plaintext password for user '{USERNAME}': ")
NET_USERNAME = input("Enter device login username: ")
NET_PASSWORD = getpass(f"Enter login password for '{NET_USERNAME}': ")

# === LOAD AND CLEAN EXCEL DATA ===
df = pd.read_excel(EXCEL_PATH)
df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]

# Identify columns
ip_col = next((c for c in df.columns if "ip" in c), None)
host_col = next((c for c in df.columns if "host" in c), None)
device_col = next((c for c in df.columns if "device" in c or "type" in c), None)

# Fail fast if any required column is missing
if ip_col is None:
    raise ValueError("Could not find an IP address column in the Excel file.")
if host_col is None:
    raise ValueError("Could not find a Host column in the Excel file.")
if device_col is None:
    raise ValueError("Could not find a Device/Type column in the Excel file.")

# Drop rows with missing IP or Host
df = df.dropna(subset=[ip_col, host_col])

# Filter only HP ProCurve switches
df = df[df[device_col].str.lower().str.contains("procurve", na=False)]

# === DEFINE COMMAND BLOCK ===
def user_creation_cmds(username, password):
    return [
        "",  # send ENTER to get prompt
        "system-view",
        f"password operator user-name {username} plaintext {password}",
        f"password manager user-name {username} plaintext {password}"
    ]

# === MAIN SCRIPT LOOP ===
for _, row in df.iterrows():
    ip = row[ip_col]
    hostname = row[host_col]

    print(f"\n[INFO] Connecting to {hostname} ({ip})...")

    try:
        conn = ConnectHandler(
            device_type="hp_procurve",
            ip=ip,
            username=NET_USERNAME,
            password=NET_PASSWORD,
            secret=NET_PASSWORD
        )

        conn.write_channel("\n")
        user_output = conn.send_command("show running-config | include user-name", delay_factor=4)

        # Create user
        for cmd in user_creation_cmds(USERNAME, USER_PASS):
            conn.send_command_timing(cmd)

        # Display user list
        time.sleep(2)
        user_output = conn.send_command("display current-configuration | include user-name", delay_factor=4)

        # Save configuration
        conn.send_command_timing("save")
        conn.send_command_timing("y")
        conn.send_command_timing("\n")
        conn.send_command_timing("y")

        # Save logs
        log_path = os.path.join(LOG_DIR, f"{hostname}_{ip}_user_create.log")
        with open(log_path, "w") as f:
            f.write(f"Device: {hostname} ({ip})\n")
            f.write(f"User Created: {USERNAME}\n")
            f.write(f"Timestamp: {datetime.now()}\n\n")
            f.write("--- Display User Output ---\n")
            f.write(user_output)

        print(f"[SUCCESS] User created and config saved on {hostname}. Log saved: {log_path}")
        conn.disconnect()

    except Exception as e:
        print(f"[ERROR] {hostname} ({ip}): {e}")
