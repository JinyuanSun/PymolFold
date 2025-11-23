"""PymolFold: for API-driven Structure Prediction and Quality Assessment.

Developed by Jinyuan Sun and Yifan Deng.
"""

import sys
import subprocess
import json
import urllib.request
from importlib import metadata
from packaging import version
from pathlib import Path

# from pymol import cmd as pymol_cmd, plugins
from pymol.Qt import QtWidgets, QtCore


def get_latest_pypi_version(pkg_name):
    """
    Query PyPI to find the latest version of the package.
    """
    url = f"https://pypi.org/pypi/{pkg_name}/json"
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.loads(response.read().decode())
            return data["info"]["version"]
    except Exception as e:
        print(f"Warning: Could not check latest version for {pkg_name}: {e}")
        return None


def ensure_package(pkg_name):
    """
    Ensure that the package is installed.
    Checks current version against PyPI latest version.
    Only installs/upgrades if necessary.
    """
    python_exe = sys.executable
    if python_exe.endswith("pythonw.exe"):
        python_exe = python_exe.replace("pythonw.exe", "python.exe")

    # 1. Get the latest version from PyPI
    latest_version_str = get_latest_pypi_version(pkg_name)

    # 2. Check current installation
    current_version_str = None
    try:
        current_version_str = metadata.version(pkg_name)
    except metadata.PackageNotFoundError:
        pass

    # 3. Determine action
    should_install = False

    if current_version_str is None:
        print(f"[{pkg_name}] Not found. Installing latest version...")
        should_install = True
    elif latest_version_str:
        # Compare versions using 'packaging.version' to handle semantic versioning correctly
        if version.parse(latest_version_str) > version.parse(current_version_str):
            print(
                f"[{pkg_name}] Found version {current_version_str}. Upgrading to {latest_version_str}..."
            )
            should_install = True
        else:
            print(f"[{pkg_name}] Version {current_version_str} is up to date.")
    else:
        # Fallback if network check fails but package exists: Do nothing or force upgrade?
        # Usually better to stay safe and do nothing if we can't verify an update exists.
        print(
            f"[{pkg_name}] Version {current_version_str} installed. Skipping update check (network issue)."
        )

    # 4. Execute Installation if needed
    if should_install:
        try:
            subprocess.check_call(
                [
                    python_exe,
                    "-m",
                    "pip",
                    "install",
                    "--upgrade",
                    pkg_name,
                    "--index-url",
                    "https://pypi.org/simple",
                ]
            )
            print("---------------------------------------------------------------")
            print(f"SUCCESS: {pkg_name} has been updated/installed.")
            print("Please check the latest documentation and changes at:")
            print("https://github.com/JinyuanSun/PymolFold/blob/main/README.md")
            print("---------------------------------------------------------------")
        except subprocess.CalledProcessError as e:
            print(f"ERROR: Failed to install {pkg_name}. details: {e}")


# Ensure pymolfold is installed or upgraded to latest
ensure_package("pymolfold")

import pymolfold

# Add package root to Python path
PACKAGE_ROOT = Path(__file__).parent
if str(PACKAGE_ROOT) not in sys.path:
    # OMG, have to append instead of insert here. If you test on Windows, this will overwrite the PDB module called in Torch.
    # Because PyMol itself has a PDB file, you may get "attempted relative import with no known parent package"
    sys.path.append(str(PACKAGE_ROOT))

# Initialize plugin
pymolfold.plugin.__init_plugin__()


class PymolFoldDialog(QtWidgets.QDialog):
    """
    Qt-based GUI front-end for the PymolFold command-line plugin.
    Wraps query_esm3, query_esmfold, query_boltz_monomer, fetch_af, fetch_am,
    set_workdir, set_api_key, and foldingui.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("PymolFold – Structure Prediction")
        self.resize(700, 500)

        self._build_ui()
        self._connect_signals()

        # Make sure we start with the current global ABS_PATH
        try:
            self.workdir_edit.setText(pymolfold.plugin.ABS_PATH)
        except NameError:
            pass

    # ---------- UI construction ----------

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)

        tabs = QtWidgets.QTabWidget()
        layout.addWidget(tabs)

        # --- Tab 1: Prediction ---
        pred_widget = QtWidgets.QWidget()
        pred_layout = QtWidgets.QGridLayout(pred_widget)

        row = 0
        pred_layout.addWidget(QtWidgets.QLabel("Amino acid sequence:"), row, 0, 1, 3)
        row += 1
        self.seq_edit = QtWidgets.QPlainTextEdit()
        self.seq_edit.setPlaceholderText("Enter amino acid sequence here…")
        self.seq_edit.setTabChangesFocus(True)
        pred_layout.addWidget(self.seq_edit, row, 0, 1, 3)

        row += 1
        pred_layout.addWidget(QtWidgets.QLabel("Name (optional):"), row, 0)
        self.name_edit = QtWidgets.QLineEdit()
        self.name_edit.setPlaceholderText(
            "If empty, name will be derived from sequence"
        )
        pred_layout.addWidget(self.name_edit, row, 1, 1, 2)

        row += 1
        pred_layout.addWidget(QtWidgets.QLabel("Predictor:"), row, 0)

        self.predictor_combo = QtWidgets.QComboBox()
        self.predictor_combo.addItems(["ESM-3", "ESMFold", "Boltz2 (monomer + MSA)"])
        pred_layout.addWidget(self.predictor_combo, row, 1, 1, 2)

        # ESM-3 extra options
        row += 1
        self.temp_spin = QtWidgets.QDoubleSpinBox()
        self.temp_spin.setRange(0.0, 2.0)
        self.temp_spin.setSingleStep(0.1)
        self.temp_spin.setValue(0.7)

        self.num_steps_spin = QtWidgets.QSpinBox()
        self.num_steps_spin.setRange(1, 64)
        self.num_steps_spin.setValue(8)

        self.model_name_edit = QtWidgets.QLineEdit("esm3-medium-2024-08")

        pred_layout.addWidget(QtWidgets.QLabel("Temperature:"), row, 0)
        pred_layout.addWidget(self.temp_spin, row, 1)

        row += 1
        pred_layout.addWidget(QtWidgets.QLabel("Num steps:"), row, 0)
        pred_layout.addWidget(self.num_steps_spin, row, 1)

        row += 1
        pred_layout.addWidget(QtWidgets.QLabel("ESM-3 model name:"), row, 0)
        pred_layout.addWidget(self.model_name_edit, row, 1, 1, 2)

        row += 1
        self.run_button = QtWidgets.QPushButton("Run prediction")
        pred_layout.addWidget(self.run_button, row, 0, 1, 3)

        tabs.addTab(pred_widget, "Prediction")

        # --- Tab 2: Fetch structures ---
        fetch_widget = QtWidgets.QWidget()
        fetch_layout = QtWidgets.QGridLayout(fetch_widget)

        row = 0
        fetch_layout.addWidget(
            QtWidgets.QLabel("Fetch AlphaFold by UniProt ID:"), row, 0
        )
        self.af_uniprot_edit = QtWidgets.QLineEdit()
        self.af_uniprot_edit.setPlaceholderText("e.g. P0DTC2")
        fetch_layout.addWidget(self.af_uniprot_edit, row, 1)
        self.af_fetch_btn = QtWidgets.QPushButton("Fetch AF model")
        fetch_layout.addWidget(self.af_fetch_btn, row, 2)

        row += 1
        fetch_layout.addWidget(
            QtWidgets.QLabel("Fetch AlphaMissense (Heglelab):"), row, 0
        )
        self.am_name_edit = QtWidgets.QLineEdit()
        self.am_name_edit.setPlaceholderText(
            "e.g. BRCA1_p.Gly24Arg (whatever API expects)"
        )
        fetch_layout.addWidget(self.am_name_edit, row, 1)
        self.am_fetch_btn = QtWidgets.QPushButton("Fetch AM structure")
        fetch_layout.addWidget(self.am_fetch_btn, row, 2)

        tabs.addTab(fetch_widget, "Fetch")

        # --- Tab 3: Settings / Utilities ---
        settings_widget = QtWidgets.QWidget()
        settings_layout = QtWidgets.QGridLayout(settings_widget)

        row = 0
        settings_layout.addWidget(QtWidgets.QLabel("Working directory:"), row, 0)
        self.workdir_edit = QtWidgets.QLineEdit()
        settings_layout.addWidget(self.workdir_edit, row, 1)
        self.workdir_browse_btn = QtWidgets.QPushButton("Browse…")
        settings_layout.addWidget(self.workdir_browse_btn, row, 2)

        row += 1
        self.set_workdir_btn = QtWidgets.QPushButton("Set workdir")
        settings_layout.addWidget(self.set_workdir_btn, row, 0, 1, 3)

        row += 1
        settings_layout.addWidget(QtWidgets.QLabel("API key name:"), row, 0)
        self.api_name_edit = QtWidgets.QLineEdit("ESM_API_TOKEN")
        settings_layout.addWidget(self.api_name_edit, row, 1, 1, 2)

        row += 1
        settings_layout.addWidget(QtWidgets.QLabel("API key value:"), row, 0)
        self.api_value_edit = QtWidgets.QLineEdit()
        self.api_value_edit.setEchoMode(QtWidgets.QLineEdit.Password)
        settings_layout.addWidget(self.api_value_edit, row, 1, 1, 2)

        row += 1
        self.set_api_btn = QtWidgets.QPushButton("Set & save API key")
        settings_layout.addWidget(self.set_api_btn, row, 0, 1, 3)

        row += 1
        self.open_webui_btn = QtWidgets.QPushButton("Open Streamlit UI (foldingui)")
        settings_layout.addWidget(self.open_webui_btn, row, 0, 1, 3)

        tabs.addTab(settings_widget, "Settings")

        # --- Log output ---
        self.log_edit = QtWidgets.QPlainTextEdit()
        self.log_edit.setReadOnly(True)
        self.log_edit.setPlaceholderText("Log output (in addition to PyMOL console)…")
        layout.addWidget(self.log_edit)

        # Close button
        btn_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Close)
        btn_box.rejected.connect(self.close)
        layout.addWidget(btn_box)

    # ---------- Signal connections ----------

    def _connect_signals(self):
        self.run_button.clicked.connect(self.on_run_prediction)
        self.af_fetch_btn.clicked.connect(self.on_fetch_af)
        self.am_fetch_btn.clicked.connect(self.on_fetch_am)

        self.workdir_browse_btn.clicked.connect(self.on_browse_workdir)
        self.set_workdir_btn.clicked.connect(self.on_set_workdir)

        self.set_api_btn.clicked.connect(self.on_set_api_key)
        self.open_webui_btn.clicked.connect(self.on_open_webui)

        self.predictor_combo.currentIndexChanged.connect(self._on_predictor_changed)
        self._on_predictor_changed(self.predictor_combo.currentIndex())

    # ---------- Helpers ----------

    def append_log(self, text: str):
        self.log_edit.appendPlainText(text)
        self.log_edit.verticalScrollBar().setValue(
            self.log_edit.verticalScrollBar().maximum()
        )

    def _on_predictor_changed(self, idx: int):
        """Enable/disable ESM-3 specific settings."""
        is_esm3 = self.predictor_combo.currentText() == "ESM-3"
        self.temp_spin.setEnabled(is_esm3)
        self.num_steps_spin.setEnabled(is_esm3)
        self.model_name_edit.setEnabled(is_esm3)

    # ---------- Slots / actions ----------

    def on_run_prediction(self):
        seq = self.seq_edit.toPlainText().strip()
        if not seq:
            QtWidgets.QMessageBox.warning(
                self, "No sequence", "Please enter a sequence."
            )
            return

        name = self.name_edit.text().strip() or None
        predictor = self.predictor_combo.currentText()

        self.append_log(f"Starting prediction with {predictor}…")

        # Run in a background thread so the GUI doesn't freeze.
        def worker():
            try:
                if predictor == "ESM-3":
                    temperature = float(self.temp_spin.value())
                    num_steps = int(self.num_steps_spin.value())
                    model_name = (
                        self.model_name_edit.text().strip() or "esm3-medium-2024-08"
                    )
                    self.append_log("Calling query_esm3(...)")
                    pymolfold.plugin.query_esm3(
                        sequence=seq,
                        name=name,
                        temperature=temperature,
                        num_steps=num_steps,
                        model_name=model_name,
                    )
                elif predictor == "ESMFold":
                    self.append_log("Calling query_esmfold(...)")
                    pymolfold.plugin.query_esmfold(sequence=seq, name=name)
                else:
                    self.append_log("Calling query_boltz_monomer(...)")
                    pymolfold.plugin.query_boltz_monomer(sequence=seq, name=name)

                self.append_log("Prediction finished. Check PyMOL viewer and console.")
            except Exception as e:
                self.append_log(f"Error: {e}")

        import threading

        threading.Thread(target=worker, daemon=True).start()

    def on_fetch_af(self):
        uniprot_id = self.af_uniprot_edit.text().strip()
        if not uniprot_id:
            QtWidgets.QMessageBox.warning(
                self, "Missing UniProt ID", "Enter a UniProt ID."
            )
            return

        self.append_log(f"Fetching AlphaFold model for {uniprot_id}…")

        def worker():
            try:
                pymolfold.plugin.fetch_af(uniprot_id)
                self.append_log("AlphaFold model loaded into PyMOL.")
            except Exception as e:
                self.append_log(f"Error fetching AF model: {e}")

        import threading

        threading.Thread(target=worker, daemon=True).start()

    def on_fetch_am(self):
        name = self.am_name_edit.text().strip()
        if not name:
            QtWidgets.QMessageBox.warning(
                self, "Missing name", "Enter a name / identifier."
            )
            return

        self.append_log(f"Fetching AlphaMissense structure for {name}…")

        def worker():
            try:
                pymolfold.plugin.query_am_hegelab(name)
                self.append_log("AlphaMissense structure loaded into PyMOL.")
            except Exception as e:
                self.append_log(f"Error fetching AlphaMissense structure: {e}")

        import threading

        threading.Thread(target=worker, daemon=True).start()

    def on_browse_workdir(self):
        path = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Select working directory", self.workdir_edit.text() or ""
        )
        if path:
            self.workdir_edit.setText(path)

    def on_set_workdir(self):
        path = self.workdir_edit.text().strip()
        if not path:
            QtWidgets.QMessageBox.warning(
                self, "No path", "Please select or enter a working directory."
            )
            return
        try:
            pymolfold.plugin.set_workdir(path)
            self.append_log(f"Working directory set to: {path}")
        except Exception as e:
            self.append_log(f"Error setting workdir: {e}")

    def on_set_api_key(self):
        key_name = self.api_name_edit.text().strip()
        key_value = self.api_value_edit.text().strip()

        if not key_name or not key_value:
            QtWidgets.QMessageBox.warning(
                self, "Missing fields", "Please provide both key name and value."
            )
            return

        try:
            pymolfold.plugin.set_api_key(key_name, key_value)
            self.append_log(f"API key {key_name} set and saved to .env.")
            self.api_value_edit.clear()
        except Exception as e:
            self.append_log(f"Error setting API key: {e}")

    def on_open_webui(self):
        """
        Calls your existing `init_boltz2_gui` / foldingui function which launches the
        FastAPI + Streamlit UI in a browser.
        """
        self.append_log("Launching Streamlit UI (foldingui)…")

        def worker():
            try:
                pymolfold.plugin.init_boltz2_gui()
                self.append_log("Streamlit UI requested (check browser).")
            except Exception as e:
                self.append_log(f"Error launching Streamlit UI: {e}")

        import threading

        threading.Thread(target=worker, daemon=True).start()


def show_pymolfold_dialog():
    """
    Create or raise the Qt dialog from the PyMOL plugin menu.
    """
    from pymol import plugins

    # from pymolfold.plugin import PymolFoldDialog

    global _pymolfold_dialog

    # Parent to PyMOL main window if available
    parent = plugins.get_qtwindow() if hasattr(plugins, "get_qtwindow") else None

    # if _pymolfold_dialog is None or not _pymolfold_dialog.isVisible():
    _pymolfold_dialog = PymolFoldDialog(parent=parent)
    _pymolfold_dialog.show()
    _pymolfold_dialog.raise_()
    _pymolfold_dialog.activateWindow()


def __init_plugin__(app=None):
    """Initialize the PymolFold plugin in PyMOL."""
    from pymol.plugins import addmenuitemqt

    addmenuitemqt("PymolFold Streamlit GUI", pymolfold.plugin.init_boltz2_gui)
    addmenuitemqt("PymolFold PyQt GUI", show_pymolfold_dialog)
