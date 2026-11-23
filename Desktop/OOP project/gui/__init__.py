"""Member 5 - Tkinter interface package."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

# Load the original implementation without copying or renaming it.
_GUI_PATH = Path(__file__).resolve().parent.parent / "gui.py"
_SPEC = spec_from_file_location("_pharmacy_gui", _GUI_PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"Could not load Tkinter implementation at {_GUI_PATH}")
_GUI_IMPL = module_from_spec(_SPEC)
_SPEC.loader.exec_module(_GUI_IMPL)

PharmacyApp = _GUI_IMPL.PharmacyApp
MainMenuFrame = _GUI_IMPL.MainMenuFrame
BaseScreen = _GUI_IMPL.BaseScreen
RegisterMedicineFrame = _GUI_IMPL.RegisterMedicineFrame
RegisterBranchFrame = _GUI_IMPL.RegisterBranchFrame
ReceiveStockFrame = _GUI_IMPL.ReceiveStockFrame
CreatePrescriptionFrame = _GUI_IMPL.CreatePrescriptionFrame
DispenseFrame = _GUI_IMPL.DispenseFrame
CancelPrescriptionFrame = _GUI_IMPL.CancelPrescriptionFrame
TransferStockFrame = _GUI_IMPL.TransferStockFrame
LowStockFrame = _GUI_IMPL.LowStockFrame


def main() -> None:
    _GUI_IMPL.main()
