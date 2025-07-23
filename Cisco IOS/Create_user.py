import pandas as pd
from netmiko import ConnectHandler
from getpass import getpass
from datetime import datetime
import os

# === CONFIGURATION ===
EXCEL_PATH = r"C:\Users\Imran sarwar\Documents\randome project\network_device-scripts\scripts_get_config\get from csv\devices.xlsx"
LOG_DIR = r"C:\Users\Imran sarwar\Documents\randome project\network_device-scripts\scripts_get_config\get from csv\logs\user_creation"


new_username = input("Enter the NEW username to create: ")
new_password = getpass("Enter password for the new user: ")

# Ensure log directory exists
os.makedirs(LOG_DIR, exist_ok=True)

# Prompt for credentials used for connecting
print("Enter credentials to connect to Cisco IOS devices:")
net_username = input("Username: ")
net_password = getpass("Password: ")

# Read and filter Cisco IOS devices
df = pd.read_excel(EXCEL_PATH)
df = df.rename(columns={
    'Device Type': 'device_type',
    'IP Address': 'ip',
    'Hostname': 'hostname'
})
df_ios = df[df['device_type'].str.lower() == 'cisco ios'].dropna(subset=['ip', 'hostname'])

print(f"\n[INFO] Found {len(df_ios)} Cisco IOS devices.\n")

for idx, row in df_ios.iterrows():
    ip = row['ip']
    hostname = row['hostname']

    print(f"→ Connecting to {hostname} ({ip})...")

    device = {
        'device_type': 'cisco_ios',
        'ip': ip,
        'username': net_username,
        'password': net_password,
        'secret': net_password,  # in case enable is required
    }

    try:
        conn = ConnectHandler(**device)
        conn.enable()

        # Create new user
        config_commands = [
            f'username {new_username} privilege 15 secret {new_password}'
        ]
        conn.send_config_set(config_commands)

        # Show existing users
        output = conn.send_command("show run | i username")

        # Write memory
        conn.save_config()

        # Save log
        log_path = os.path.join(LOG_DIR, f"{hostname}_{ip}_log.txt")
        with open(log_path, "w") as f:
            f.write(f"Log for {hostname} ({ip}) - {datetime.now()}\n")
            f.write("\n--- User Configurations ---\n")
            f.write(output)

        print(f"[SUCCESS] User created on {hostname} ({ip}) and log saved.\n")
        conn.disconnect()

    except Exception as e:
        print(f"[ERROR] Failed to connect to {hostname} ({ip}): {e}\n")
