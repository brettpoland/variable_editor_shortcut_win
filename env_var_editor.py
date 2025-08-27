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

class VariableDialog(QtWidgets.QDialog):
    def __init__(self, name="", value="", scope="user", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Variable")
        layout = QtWidgets.QFormLayout(self)
        self.name_edit = QtWidgets.QLineEdit(name)
        self.value_edit = QtWidgets.QLineEdit(value)
        self.scope_combo = QtWidgets.QComboBox()
        self.scope_combo.addItems(["user", "system"])
        self.scope_combo.setCurrentText(scope)
        layout.addRow("Name:", self.name_edit)
        layout.addRow("Value:", self.value_edit)
        layout.addRow("Scope:", self.scope_combo)
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_data(self):
        return (
            self.name_edit.text(),
            self.value_edit.text(),
            self.scope_combo.currentText(),
        )

class EnvVarEditor(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Environment Variable Editor")
        self.resize(600, 400)
        layout = QtWidgets.QVBoxLayout(self)
        self.table = QtWidgets.QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Name", "Value", "Scope"])
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
        self.add_btn.clicked.connect(self.add_variable)
        self.edit_btn.clicked.connect(self.edit_variable)
        self.remove_btn.clicked.connect(self.remove_variable)
        self.refresh_btn.clicked.connect(self.load_variables)
        self.load_variables()

    def load_variables(self):
        self.table.setRowCount(0)
        for scope in ["user", "system"]:
            try:
                vars = read_variables(scope)
            except EnvironmentError:
                vars = {}
            for name, value in vars.items():
                row = self.table.rowCount()
                self.table.insertRow(row)
                self.table.setItem(row, 0, QtWidgets.QTableWidgetItem(name))
                self.table.setItem(row, 1, QtWidgets.QTableWidgetItem(value))
                self.table.setItem(row, 2, QtWidgets.QTableWidgetItem(scope))

    def add_variable(self):
        dlg = VariableDialog(parent=self)
        if dlg.exec_():
            name, value, scope = dlg.get_data()
            set_variable(name, value, scope)
            self.load_variables()

    def edit_variable(self):
        row = self.table.currentRow()
        if row < 0:
            return
        name = self.table.item(row, 0).text()
        value = self.table.item(row, 1).text()
        scope = self.table.item(row, 2).text()
        dlg = VariableDialog(name, value, scope, self)
        if dlg.exec_():
            new_name, new_value, new_scope = dlg.get_data()
            if new_name != name or new_scope != scope:
                delete_variable(name, scope)
            set_variable(new_name, new_value, new_scope)
            self.load_variables()

    def remove_variable(self):
        row = self.table.currentRow()
        if row < 0:
            return
        name = self.table.item(row, 0).text()
        scope = self.table.item(row, 2).text()
        delete_variable(name, scope)
        self.load_variables()


def main():
    if os.name != 'nt':
        raise EnvironmentError("This application must be run on Windows")
    app = QtWidgets.QApplication(sys.argv)
    editor = EnvVarEditor()
    editor.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
