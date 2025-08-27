# Environment Variable Editor

A simple PyQt-based GUI for adding, editing, and removing user or system environment variables on Windows 11.

## Requirements
- Python 3
- PyQt5

## Usage
Run the application on Windows:

```bash
python env_var_editor.py
```

The table displays user and system variables. Use **Add**, **Edit**, **Remove**, and **Refresh** buttons to manage variables. Changes are written to the registry and broadcast so new processes receive the updates.
