# Environment Variable Editor

A simple PyQt-based GUI for viewing and modifying entries in the **user** `PATH` variable on Windows 11.

## Requirements
- Python 3
- PyQt5

## Usage
Run the application on Windows:

```bash
python env_var_editor.py
```

The table displays the existing entries in the user's `PATH` variable. Use **Add**, **Edit**, **Remove**, and **Refresh** buttons to manage these entries. Changes are written to the registry and broadcast so new processes receive the updates.
