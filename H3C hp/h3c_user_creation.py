import pandas as pd
from netmiko import ConnectHandler
from getpass import getpass
from datetime import datetime
import os
import time

# === Configuration ===
EXCEL_PATH = r"h3c_switches_filtered.xlsx"  # <- Excel file path
LOG_DIR = "h3c_user_creation_logs"
os.makedirs(LOG_DIR, exist_ok=True)



# === User Input ===
USERNAME = input("Enter the username to create: ")
PASSWORD = getpass(f"Enter the password for {USERNAME}: ")
NET_USERNAME = input("Enter device login username: ")
NET_PASSWORD = getpass(f"Enter login password for {NET_USERNAME}: ")

# === Load Filtered Excel ===
df = pd.read_excel(EXCEL_PATH)
df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]

ip_col = next((c for c in df.columns if "ip" in c), None)
host_col = next((c for c in df.columns if "host" in c), None)

df = df.dropna(subset=[ip_col, host_col])

print(f"[INFO] Valid devices to process: {len(df)}")

# === Command Block ===
def user_creation_cmds(username, password):
    return [
        "system-view",
        f"local-user {username} class manage",
        f"password simple {password}",
        "authorization-attribute user-role level-3",
        "service-type ssh terminal",
        "service-type ftp"
    ]

# === Process Each Device ===
for _, row in df.iterrows():
    ip = row[ip_col]
    hostname = row[host_col] if host_col else ip
    print(f"Connecting to {hostname} ({ip})...")

    try:
        conn = ConnectHandler(
            device_type="hp_comware",
            ip=ip,
            username=NET_USERNAME,
            password=NET_PASSWORD,
            secret=NET_PASSWORD
        )

        conn.write_channel("\n")
        conn.read_until_prompt()

        for cmd in user_creation_cmds(USERNAME, PASSWORD):
            conn.send_command_timing(cmd)
        
        time.sleep(1)

        user_block = conn.send_command("display current-configuration | section local-user", delay_factor=2)

        # Save configuration
        conn.send_command_timing("save")
        conn.send_command_timing("y")
        conn.send_command_timing("\n")
        conn.send_command_timing("y")

        # Capture config
        
        log_file = os.path.join(LOG_DIR, f"{hostname}_{ip}_user_create.log")
        with open(log_file, "w") as f:
            f.write(f"Device: {hostname} ({ip})\n")
            f.write(f"User Created: {USERNAME}\n")
            f.write(f"Timestamp: {datetime.now()}\n")
            f.write("--- User Configuration Block ---\n")
            f.write(user_block)

        print(f"[SUCCESS] User created on {hostname}, log saved to {log_file}\n")
        conn.disconnect()

    except Exception as e:
        print(f"[ERROR] {hostname} ({ip}): {e}")
