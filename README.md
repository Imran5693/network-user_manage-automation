# network-user_manage-automation
## Multi-Vendor Network User Automation

This is a demo project showcasing automation scripts for managing user accounts (create/delete) across various network devices (Cisco, HP, H3C, Brocade).

> ⚠️ All IPs, credentials, and test cases are based on lab environments. No production data included.

### Features
- Modular scripts for user operations
- Vendor-specific CLI command handling
- Built using Netmiko 

### Use Cases
- Consistent user provisioning in multi-vendor environments
- Pre/Post-check integrations possible
- Designed during freelance automation tasks

### Vendor Notes

- **Cisco, HP (Comware), H3C, Brocade:** Full support for user creation and deletion via CLI.
- **HP ProCurve:** Only supports changing passwords for predefined user roles like `manager` or `operator`. ProCurve CLI does not support creating new usernames.  
  > 🔒 Example: `password operator user-name` can be used to change the manager password.
