import pandas as pd
from netmiko import ConnectHandler
from getpass import getpass
from datetime import datetime
import os

# === CONFIGURATION ===
EXCEL_PATH = r"C:\python_folder\devices.xlsx"  # <-- Update path as needed
BASE_LOG_DIR = "brocade_user_logs"

# === USER INPUT ===
mode = input("Enter mode (create/delete): ").strip().lower()
if mode not in ["create", "delete"]:
    print("[ERROR] Invalid mode. Must be 'create' or 'delete'")
    exit(1)

username = input(f"Enter the username to {mode}: ").strip()
password = getpass(f"Enter password for user '{username}': ") if mode == "create" else None

net_user = input("Enter device login username: ").strip()
net_pass = getpass(f"Enter login password for '{net_user}': ")

# === LOAD AND FILTER EXCEL ===
try:
    df = pd.read_excel(EXCEL_PATH)
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    ip_col = next((c for c in df.columns if "ip" in c), None)
    host_col = next((c for c in df.columns if "host" in c), None)
    device_col = next((c for c in df.columns if "device" in c or "type" in c), None)

    df = df.dropna(subset=[ip_col, host_col, device_col])
    brocade_df = df[df[device_col].str.lower().str.contains("brocade", na=False)].copy()

    if brocade_df.empty:
        print("[INFO] No Brocade devices found in the Excel file.")
        exit(0)

except Exception as e:
    print(f"[ERROR] Failed to load Excel: {e}")
    exit(1)

print(f"\n[INFO] Total Brocade devices found: {len(brocade_df)}")

# === LOG DIRECTORY ===
mode_log_dir = os.path.join(BASE_LOG_DIR, f"user_{mode}")
os.makedirs(mode_log_dir, exist_ok=True)


# === ACTION FUNCTIONS ===

def create_user(conn, username, password, os_version):
    conn.send_command_timing("config t")
    if os_version.startswith("07.2"):
        # Interactive mode for 7.2.x
        conn.send_command_timing(f"username {username} privilege 0 password")
        conn.send_command_timing(password)
    else:
        # Single line for 7.3.x or higher
        conn.send_command_timing(f"username {username} privilege 0 password {password}")
    conn.send_command_timing("end")
    conn.send_command_timing("wr memory")


def delete_user(conn, username):
    conn.send_command_timing("config t")
    conn.send_command_timing(f"no username {username}")
    conn.send_command_timing("end")
    conn.send_command_timing("wr memory")


# === MAIN LOOP ===
for _, row in brocade_df.iterrows():
    ip = str(row[ip_col]).strip()
    hostname = str(row[host_col]).strip()

    print(f"\n[INFO] Connecting to {hostname} ({ip})...")

    try:
        conn = ConnectHandler(
            device_type="brocade_fastiron",
            ip=ip,
            username=net_user,
            password=net_pass,
            secret=net_pass
        )

        # Get OS version
        version_output = conn.send_command("show version", delay_factor=2)
        os_version = "unknown"
        for line in version_output.splitlines():
            if "SW: Version" in line or "SW:" in line:
                os_version = line.split("SW:")[-1].strip().split()[1]
                break

        print(f"[INFO] Detected OS Version: {os_version}")

        # Perform create or delete
        if mode == "create":
            create_user(conn, username, password, os_version)
        else:
            delete_user(conn, username)

        # Show usernames after action
        user_output = conn.send_command("show run | include username", delay_factor=3)

        # Save log
        log_file = os.path.join(mode_log_dir, f"{hostname}_{ip}_{mode}.log")
        with open(log_file, "w") as f:
            f.write(f"Operation: {mode}\n")
            f.write(f"Device: {hostname} ({ip})\n")
            f.write(f"OS Version: {os_version}\n")
            f.write(f"User: {username}\n")
            f.write(f"Timestamp: {datetime.now()}\n\n")
            f.write("--- Current Users ---\n")
            f.write(user_output)

        print(f"[SUCCESS] {mode.title()} completed on {hostname}. Log saved: {log_file}")
        conn.disconnect()

    except Exception as e:
        print(f"[ERROR] {hostname} ({ip}): {e}")
