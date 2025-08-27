import os
import sys
import ctypes
from PyQt5 import QtWidgets

# Conditional import for Windows registry access
if os.name == 'nt':
    import winreg
else:
    winreg = None

REG_PATHS = {
    "user": (winreg.HKEY_CURRENT_USER if winreg else None, r"Environment"),
    "system": (winreg.HKEY_LOCAL_MACHINE if winreg else None,
               r"SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Environment"),
}

def read_variables(scope):
    if winreg is None:
        raise EnvironmentError("This application must be run on Windows")
    hive, path = REG_PATHS[scope]
    variables = {}
    with winreg.OpenKey(hive, path) as key:
        i = 0
        while True:
            try:
                name, value, _ = winreg.EnumValue(key, i)
                variables[name] = value
                i += 1
            except OSError:
                break
    return variables

def set_variable(name, value, scope):
    if winreg is None:
        raise EnvironmentError("This application must be run on Windows")
    hive, path = REG_PATHS[scope]
    with winreg.OpenKey(hive, path, 0, winreg.KEY_SET_VALUE) as key:
        winreg.SetValueEx(key, name, 0, winreg.REG_EXPAND_SZ, value)
    broadcast_change()

def delete_variable(name, scope):
    if winreg is None:
        raise EnvironmentError("This application must be run on Windows")
    hive, path = REG_PATHS[scope]
    with winreg.OpenKey(hive, path, 0, winreg.KEY_SET_VALUE) as key:
        try:
            winreg.DeleteValue(key, name)
        except FileNotFoundError:
            pass
    broadcast_change()

def broadcast_change():
    if os.name != 'nt':
        return
    HWND_BROADCAST = 0xFFFF
    WM_SETTINGCHANGE = 0x001A
    SMTO_ABORTIFHUNG = 0x0002
    ctypes.windll.user32.SendMessageTimeoutW(
        HWND_BROADCAST,
        WM_SETTINGCHANGE,
        0,
        "Environment",
        SMTO_ABORTIFHUNG,
        5000,
        None,
    )

class PathEntryDialog(QtWidgets.QDialog):
    def __init__(self, value="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("PATH Entry")
        layout = QtWidgets.QFormLayout(self)
        self.value_edit = QtWidgets.QLineEdit(value)
        layout.addRow("Value:", self.value_edit)
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_value(self):
        return self.value_edit.text()

class EnvVarEditor(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PATH Editor")
        self.resize(600, 400)
        layout = QtWidgets.QVBoxLayout(self)
        self.table = QtWidgets.QTableWidget(0, 1)
        self.table.setHorizontalHeaderLabels(["Value"])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)
        btn_layout = QtWidgets.QHBoxLayout()
        self.add_btn = QtWidgets.QPushButton("Add")
        self.edit_btn = QtWidgets.QPushButton("Edit")
        self.remove_btn = QtWidgets.QPushButton("Remove")
        self.refresh_btn = QtWidgets.QPushButton("Refresh")
        for btn in [self.add_btn, self.edit_btn, self.remove_btn, self.refresh_btn]:
            btn_layout.addWidget(btn)
        layout.addLayout(btn_layout)
        self.add_btn.clicked.connect(self.add_entry)
        self.edit_btn.clicked.connect(self.edit_entry)
        self.remove_btn.clicked.connect(self.remove_entry)
        self.refresh_btn.clicked.connect(self.load_variables)
        self.load_variables()

    def load_variables(self):
        self.table.setRowCount(0)
        try:
            vars = read_variables("user")
            path_val = ""
            for name, value in vars.items():
                if name.upper() == "PATH":
                    path_val = value
                    break
        except EnvironmentError:
            path_val = ""
        for entry in path_val.split(os.pathsep):
            if not entry:
                continue
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QtWidgets.QTableWidgetItem(entry))

    def save_variables(self):
        entries = []
        for row in range(self.table.rowCount()):
            value = self.table.item(row, 0).text()
            entries.append(value)
        set_variable("Path", os.pathsep.join(entries), "user")

    def add_entry(self):
        dlg = PathEntryDialog(parent=self)
        if dlg.exec_():
            value = dlg.get_value()
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QtWidgets.QTableWidgetItem(value))
            self.save_variables()

    def edit_entry(self):
        row = self.table.currentRow()
        if row < 0:
            return
        value = self.table.item(row, 0).text()
        dlg = PathEntryDialog(value, self)
        if dlg.exec_():
            new_value = dlg.get_value()
            self.table.item(row, 0).setText(new_value)
            self.save_variables()

    def remove_entry(self):
        row = self.table.currentRow()
        if row < 0:
            return
        self.table.removeRow(row)
        self.save_variables()


def main():
    if os.name != 'nt':
        raise EnvironmentError("This application must be run on Windows")
    app = QtWidgets.QApplication(sys.argv)
    editor = EnvVarEditor()
    editor.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
