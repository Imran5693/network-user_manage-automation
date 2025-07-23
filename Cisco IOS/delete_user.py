import pandas as pd
from netmiko import ConnectHandler
from getpass import getpass
from datetime import datetime
import os

# Configuration
DEVICE_LIST = r"C:\Users\Imran sarwar\Documents\randome project\network_device-scripts\scripts_get_config\get from csv\devices.xlsx"
LOG_DIR = r"C:\Users\Imran sarwar\Documents\randome project\network_device-scripts\scripts_get_config\get from csv\logs\user_deletion"

# Authentication
ADMIN_USER = input("Enter admin username: ")
ADMIN_PASS = getpass("Enter admin password: ")
USER_TO_DELETE = input("Enter username to delete: ")

# Prepare environment
os.makedirs(LOG_DIR, exist_ok=True)

# Load device inventory
devices = pd.read_excel(DEVICE_LIST).rename(columns={
    'Device Type': 'device_type',
    'IP Address': 'ip',
    'Hostname': 'hostname'
}).query("device_type.str.lower() == 'cisco ios'").dropna(subset=['ip', 'hostname'])

print(f"\nInitiating deletion of user '{USER_TO_DELETE}' from {len(devices)} devices\n")

for _, device in devices.iterrows():
    print(f"Processing {device['hostname']} ({device['ip']})...")
    
    try:
        # Device connection
        net_device = {
            'device_type': 'cisco_ios',
            'host': device['ip'],
            'username': ADMIN_USER,
            'password': ADMIN_PASS,
            'secret': ADMIN_PASS,
            'timeout': 30,
            'session_log': os.path.join(LOG_DIR, f"{device['hostname']}_session.log")
        }
        
        # Execute deletion
        with ConnectHandler(**net_device) as conn:
            conn.enable()
            conn.send_command_timing("configure terminal")
            conn.send_command_timing(f"no username {USER_TO_DELETE}")
            conn.send_command_timing("")  # Confirm deletion
            conn.send_command_timing("end")
            conn.save_config()
            
            # Log results
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_content = f"""Operation: User Deletion
Device: {device['hostname']} ({device['ip']})
Timestamp: {timestamp}
Deleted User: {USER_TO_DELETE}
Current Users:
{conn.send_command("show run | include username")}"""
            
            with open(os.path.join(LOG_DIR, f"{device['hostname']}_deletion.log"), 'w') as f:
                f.write(log_content)
        
        print(f"{USER_TO_DELETE} Deleted successfully on {device['hostname']}({device['ip']})\n")
        
    except Exception as e:
        error_log = f"Failed on {device['hostname']} ({device['ip']}): {str(e)}"
        with open(os.path.join(LOG_DIR, f"{device['hostname']}_error.log"), 'w') as f:
            f.write(error_log)
        print(f"Error: {error_log}\n")