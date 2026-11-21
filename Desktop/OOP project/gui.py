"""
gui.py
------
Milestone 3: the Tkinter desktop application.

Design rule (see Milestone 1, section 10): no screen talks to sqlite3
directly and no screen contains business-rule logic. Every screen's job
is: collect input -> call a repository/domain method -> show the result
or the specific error message the domain layer raised. The repository
and domain classes from Milestones 1-2 are used completely unchanged.

Run with:
    python gui.py
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox

from domain import (
    Branch,
    ControlledMedicine,
    DomainError,
    OrdinaryMedicine,
    Prescription,
)
from repository import InventoryRepository


# ---------------------------------------------------------------------------
# App shell: one container frame, screens are swapped in and out of it.
# This is the standard "multi-page Tkinter app" pattern.
# ---------------------------------------------------------------------------

class PharmacyApp(tk.Tk):
    def __init__(self, repo: InventoryRepository):
        super().__init__()
        self.repo = repo
        self.title("Campus Pharmacy Inventory, Dispensing and Reporting System")
        self.geometry("720x520")

        container = ttk.Frame(self)
        container.pack(fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames: dict[type, tk.Frame] = {}
        for ScreenClass in (
            MainMenuFrame,
            RegisterMedicineFrame,
            RegisterBranchFrame,
            ReceiveStockFrame,
            CreatePrescriptionFrame,
            DispenseFrame,
            CancelPrescriptionFrame,
            TransferStockFrame,
            LowStockFrame,
        ):
            frame = ScreenClass(container, self)
            self.frames[ScreenClass] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(MainMenuFrame)

    def show_frame(self, screen_class: type) -> None:
        frame = self.frames[screen_class]
        if hasattr(frame, "refresh"):
            frame.refresh()
        frame.tkraise()


class BaseScreen(ttk.Frame):
    """Common layout: a title, a back-to-menu button, and a status label."""

    TITLE = "Screen"

    def __init__(self, parent, app: PharmacyApp):
        super().__init__(parent, padding=16)
        self.app = app
        self.repo = app.repo

        header = ttk.Frame(self)
        header.pack(fill="x", pady=(0, 12))
        ttk.Label(header, text=self.TITLE, font=("TkDefaultFont", 14, "bold")).pack(side="left")
        ttk.Button(header, text="Main Menu", command=lambda: app.show_frame(MainMenuFrame)
                   ).pack(side="right")

        self.status_var = tk.StringVar(value="")
        self.status_label = ttk.Label(self, textvariable=self.status_var, foreground="black")
        self.status_label.pack(fill="x", side="bottom", pady=(12, 0))

        self.body = ttk.Frame(self)
        self.body.pack(fill="both", expand=True)

    def set_status(self, message: str, ok: bool) -> None:
        self.status_var.set(message)
        self.status_label.configure(foreground=("#1a7f37" if ok else "#c0392b"))

    def medicine_codes(self) -> list[str]:
        return [m.code for m in self.repo.list_medicines()]

    def branch_codes(self) -> list[str]:
        return [b.code for b in self.repo.list_branches()]


# ---------------------------------------------------------------------------
# Main menu
# ---------------------------------------------------------------------------

class MainMenuFrame(ttk.Frame):
    def __init__(self, parent, app: PharmacyApp):
        super().__init__(parent, padding=24)
        ttk.Label(
            self, text="Campus Pharmacy", font=("TkDefaultFont", 18, "bold")
        ).pack(pady=(0, 24))

        buttons = [
            ("Register Medicine", RegisterMedicineFrame),
            ("Register Branch", RegisterBranchFrame),
            ("Receive Stock", ReceiveStockFrame),
            ("Create Prescription", CreatePrescriptionFrame),
            ("Dispense Prescription", DispenseFrame),
            ("Cancel Prescription", CancelPrescriptionFrame),
            ("Transfer Stock", TransferStockFrame),
            ("Low Stock Report", LowStockFrame),
        ]
        grid = ttk.Frame(self)
        grid.pack()
        for i, (label, screen_class) in enumerate(buttons):
            ttk.Button(
                grid, text=label, width=28,
                command=lambda sc=screen_class: app.show_frame(sc)
            ).grid(row=i // 2, column=i % 2, padx=8, pady=8)


# ---------------------------------------------------------------------------
# Register Medicine (FR1)
# ---------------------------------------------------------------------------

class RegisterMedicineFrame(BaseScreen):
    TITLE = "Register Medicine"

    def __init__(self, parent, app: PharmacyApp):
        super().__init__(parent, app)

        form = self.body
        self.code_var = tk.StringVar()
        self.name_var = tk.StringVar()
        self.price_var = tk.StringVar()
        self.reorder_var = tk.StringVar()
        self.type_var = tk.StringVar(value="ordinary")

        row = 0
        for label, var in [("Code", self.code_var), ("Name", self.name_var),
                            ("Unit price", self.price_var), ("Reorder level", self.reorder_var)]:
            ttk.Label(form, text=label).grid(row=row, column=0, sticky="w", pady=4)
            ttk.Entry(form, textvariable=var, width=30).grid(row=row, column=1, pady=4)
            row += 1

        ttk.Label(form, text="Type").grid(row=row, column=0, sticky="w", pady=4)
        type_frame = ttk.Frame(form)
        type_frame.grid(row=row, column=1, sticky="w")
        ttk.Radiobutton(type_frame, text="Ordinary", variable=self.type_var,
                         value="ordinary").pack(side="left")
        ttk.Radiobutton(type_frame, text="Controlled", variable=self.type_var,
                         value="controlled").pack(side="left")
        row += 1

        ttk.Button(form, text="Register", command=self.on_submit).grid(
            row=row, column=0, columnspan=2, pady=12
        )

    def on_submit(self) -> None:
        try:
            price = float(self.price_var.get())
            reorder = int(self.reorder_var.get())
            cls = ControlledMedicine if self.type_var.get() == "controlled" else OrdinaryMedicine
            medicine = cls(self.code_var.get().strip(), self.name_var.get().strip(), price, reorder)
            self.repo.save_medicine(medicine)
            self.set_status(f"Registered {medicine.code} ({medicine.medicine_type()}).", ok=True)
            self.code_var.set(""); self.name_var.set(""); self.price_var.set(""); self.reorder_var.set("")
        except ValueError as exc:
            self.set_status(f"Rejected: {exc}", ok=False)
        except DomainError as exc:
            self.set_status(f"Rejected: {exc}", ok=False)


# ---------------------------------------------------------------------------
# Register Branch (FR2)
# ---------------------------------------------------------------------------

class RegisterBranchFrame(BaseScreen):
    TITLE = "Register Branch"

    def __init__(self, parent, app: PharmacyApp):
        super().__init__(parent, app)
        form = self.body
        self.code_var = tk.StringVar()
        self.name_var = tk.StringVar()

        ttk.Label(form, text="Code").grid(row=0, column=0, sticky="w", pady=4)
        ttk.Entry(form, textvariable=self.code_var, width=30).grid(row=0, column=1, pady=4)
        ttk.Label(form, text="Name").grid(row=1, column=0, sticky="w", pady=4)
        ttk.Entry(form, textvariable=self.name_var, width=30).grid(row=1, column=1, pady=4)
        ttk.Button(form, text="Register", command=self.on_submit).grid(
            row=2, column=0, columnspan=2, pady=12
        )

    def on_submit(self) -> None:
        try:
            branch = Branch(self.code_var.get().strip(), self.name_var.get().strip())
            self.repo.save_branch(branch)
            self.set_status(f"Registered branch {branch.code}.", ok=True)
            self.code_var.set(""); self.name_var.set("")
        except (ValueError, DomainError) as exc:
            self.set_status(f"Rejected: {exc}", ok=False)


# ---------------------------------------------------------------------------
# Receive Stock (FR3)
# ---------------------------------------------------------------------------

class ReceiveStockFrame(BaseScreen):
    TITLE = "Receive Stock"

    def __init__(self, parent, app: PharmacyApp):
        super().__init__(parent, app)
        form = self.body

        ttk.Label(form, text="Medicine").grid(row=0, column=0, sticky="w", pady=4)
        self.medicine_combo = ttk.Combobox(form, state="readonly", width=27)
        self.medicine_combo.grid(row=0, column=1, pady=4)

        ttk.Label(form, text="Branch").grid(row=1, column=0, sticky="w", pady=4)
        self.branch_combo = ttk.Combobox(form, state="readonly", width=27)
        self.branch_combo.grid(row=1, column=1, pady=4)

        ttk.Label(form, text="Amount").grid(row=2, column=0, sticky="w", pady=4)
        self.amount_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.amount_var, width=30).grid(row=2, column=1, pady=4)

        ttk.Button(form, text="Receive", command=self.on_submit).grid(
            row=3, column=0, columnspan=2, pady=12
        )

    def refresh(self) -> None:
        self.medicine_combo["values"] = self.medicine_codes()
        self.branch_combo["values"] = self.branch_codes()

    def on_submit(self) -> None:
        try:
            amount = int(self.amount_var.get())
            entry = self.repo.receive_stock(self.medicine_combo.get(), self.branch_combo.get(), amount)
            self.set_status(
                f"Received {amount}. New quantity of {entry.medicine_code} at "
                f"{entry.branch_code}: {entry.quantity}.", ok=True
            )
            self.amount_var.set("")
        except (ValueError, DomainError) as exc:
            self.set_status(f"Rejected: {exc}", ok=False)


# ---------------------------------------------------------------------------
# Create Prescription (FR4)
# ---------------------------------------------------------------------------

class CreatePrescriptionFrame(BaseScreen):
    TITLE = "Create Prescription"

    def __init__(self, parent, app: PharmacyApp):
        super().__init__(parent, app)
        form = self.body
        self._lines: list[tuple[str, int]] = []

        self.patient_var = tk.StringVar()
        self.prescriber_var = tk.StringVar()

        ttk.Label(form, text="Patient ID (fictional)").grid(row=0, column=0, sticky="w", pady=4)
        ttk.Entry(form, textvariable=self.patient_var, width=27).grid(row=0, column=1, pady=4)

        ttk.Label(form, text="Branch").grid(row=1, column=0, sticky="w", pady=4)
        self.branch_combo = ttk.Combobox(form, state="readonly", width=24)
        self.branch_combo.grid(row=1, column=1, pady=4)

        ttk.Label(form, text="Prescriber code").grid(row=2, column=0, sticky="w", pady=4)
        ttk.Entry(form, textvariable=self.prescriber_var, width=27).grid(row=2, column=1, pady=4)

        line_frame = ttk.LabelFrame(form, text="Add line")
        line_frame.grid(row=3, column=0, columnspan=2, pady=12, sticky="we")

        self.line_medicine_combo = ttk.Combobox(line_frame, state="readonly", width=16)
        self.line_medicine_combo.grid(row=0, column=0, padx=4, pady=4)
        self.line_qty_var = tk.StringVar()
        ttk.Entry(line_frame, textvariable=self.line_qty_var, width=8).grid(row=0, column=1, padx=4)
        ttk.Button(line_frame, text="Add line", command=self.on_add_line).grid(row=0, column=2, padx=4)

        self.tree = ttk.Treeview(form, columns=("medicine", "qty"), show="headings", height=5)
        self.tree.heading("medicine", text="Medicine")
        self.tree.heading("qty", text="Quantity")
        self.tree.grid(row=4, column=0, columnspan=2, pady=8, sticky="we")

        ttk.Button(form, text="Submit Prescription", command=self.on_submit).grid(
            row=5, column=0, columnspan=2, pady=12
        )

    def refresh(self) -> None:
        self.branch_combo["values"] = self.branch_codes()
        self.line_medicine_combo["values"] = self.medicine_codes()

    def on_add_line(self) -> None:
        try:
            medicine_code = self.line_medicine_combo.get()
            qty = int(self.line_qty_var.get())
            if not medicine_code:
                raise ValueError("Select a medicine first.")
            if qty <= 0:
                raise ValueError("Quantity must be > 0.")
            self._lines.append((medicine_code, qty))
            self.tree.insert("", "end", values=(medicine_code, qty))
            self.line_qty_var.set("")
        except ValueError as exc:
            self.set_status(f"Could not add line: {exc}", ok=False)

    def on_submit(self) -> None:
        try:
            if not self._lines:
                raise ValueError("Add at least one line before submitting.")
            prescription = Prescription(
                self.patient_var.get().strip(), self.branch_combo.get(), self.prescriber_var.get().strip()
            )
            for medicine_code, qty in self._lines:
                prescription.add_line(medicine_code, qty)
            saved = self.repo.save_prescription(prescription)
            self.set_status(f"Saved prescription #{saved.id} (pending).", ok=True)
            self._lines.clear()
            for row_id in self.tree.get_children():
                self.tree.delete(row_id)
            self.patient_var.set(""); self.prescriber_var.set("")
        except (ValueError, DomainError) as exc:
            self.set_status(f"Rejected: {exc}", ok=False)


# ---------------------------------------------------------------------------
# Dispense (FR5-FR8)
# ---------------------------------------------------------------------------

class DispenseFrame(BaseScreen):
    TITLE = "Dispense Prescription"

    def __init__(self, parent, app: PharmacyApp):
        super().__init__(parent, app)
        form = self.body

        self.tree = ttk.Treeview(
            form, columns=("id", "patient", "branch", "prescriber"), show="headings", height=8
        )
        for col, text in [("id", "ID"), ("patient", "Patient"), ("branch", "Branch"),
                           ("prescriber", "Prescriber")]:
            self.tree.heading(col, text=text)
        self.tree.pack(fill="both", expand=True, pady=(0, 12))

        button_row = ttk.Frame(form)
        button_row.pack()
        ttk.Button(button_row, text="Refresh", command=self.refresh).pack(side="left", padx=4)
        ttk.Button(button_row, text="Dispense Selected", command=self.on_dispense).pack(side="left", padx=4)

    def refresh(self) -> None:
        for row_id in self.tree.get_children():
            self.tree.delete(row_id)
        for p in self.repo.list_pending_prescriptions():
            self.tree.insert("", "end", iid=str(p.id),
                              values=(p.id, p.patient_id, p.branch_code, p.prescriber_code))

    def on_dispense(self) -> None:
        selection = self.tree.selection()
        if not selection:
            self.set_status("Select a pending prescription first.", ok=False)
            return
        prescription_id = int(selection[0])
        try:
            dispensed = self.repo.dispense(prescription_id)
            self.set_status(f"Prescription #{dispensed.id} dispensed successfully.", ok=True)
        except DomainError as exc:
            # The transaction was rolled back inside repo.dispense(); nothing
            # changed in the database, and the prescription is still pending.
            self.set_status(f"Dispense rejected, nothing changed: {exc}", ok=False)
        self.refresh()


# ---------------------------------------------------------------------------
# Cancel Prescription (FR9, advanced)
# ---------------------------------------------------------------------------

class CancelPrescriptionFrame(BaseScreen):
    TITLE = "Cancel Prescription"

    def __init__(self, parent, app: PharmacyApp):
        super().__init__(parent, app)
        form = self.body
        self.tree = ttk.Treeview(
            form, columns=("id", "patient", "branch"), show="headings", height=8
        )
        for col, text in [("id", "ID"), ("patient", "Patient"), ("branch", "Branch")]:
            self.tree.heading(col, text=text)
        self.tree.pack(fill="both", expand=True, pady=(0, 12))

        button_row = ttk.Frame(form)
        button_row.pack()
        ttk.Button(button_row, text="Refresh", command=self.refresh).pack(side="left", padx=4)
        ttk.Button(button_row, text="Cancel Selected", command=self.on_cancel).pack(side="left", padx=4)

    def refresh(self) -> None:
        for row_id in self.tree.get_children():
            self.tree.delete(row_id)
        for p in self.repo.list_pending_prescriptions():
            self.tree.insert("", "end", iid=str(p.id), values=(p.id, p.patient_id, p.branch_code))

    def on_cancel(self) -> None:
        selection = self.tree.selection()
        if not selection:
            self.set_status("Select a pending prescription first.", ok=False)
            return
        try:
            cancelled = self.repo.cancel_prescription(int(selection[0]))
            self.set_status(f"Prescription #{cancelled.id} cancelled.", ok=True)
        except DomainError as exc:
            self.set_status(f"Rejected: {exc}", ok=False)
        self.refresh()


# ---------------------------------------------------------------------------
# Transfer Stock (FR10, advanced)
# ---------------------------------------------------------------------------

class TransferStockFrame(BaseScreen):
    TITLE = "Transfer Stock"

    def __init__(self, parent, app: PharmacyApp):
        super().__init__(parent, app)
        form = self.body

        ttk.Label(form, text="Medicine").grid(row=0, column=0, sticky="w", pady=4)
        self.medicine_combo = ttk.Combobox(form, state="readonly", width=27)
        self.medicine_combo.grid(row=0, column=1, pady=4)

        ttk.Label(form, text="From branch").grid(row=1, column=0, sticky="w", pady=4)
        self.from_combo = ttk.Combobox(form, state="readonly", width=27)
        self.from_combo.grid(row=1, column=1, pady=4)

        ttk.Label(form, text="To branch").grid(row=2, column=0, sticky="w", pady=4)
        self.to_combo = ttk.Combobox(form, state="readonly", width=27)
        self.to_combo.grid(row=2, column=1, pady=4)

        ttk.Label(form, text="Amount").grid(row=3, column=0, sticky="w", pady=4)
        self.amount_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.amount_var, width=30).grid(row=3, column=1, pady=4)

        ttk.Button(form, text="Transfer", command=self.on_submit).grid(
            row=4, column=0, columnspan=2, pady=12
        )

    def refresh(self) -> None:
        self.medicine_combo["values"] = self.medicine_codes()
        self.from_combo["values"] = self.branch_codes()
        self.to_combo["values"] = self.branch_codes()

    def on_submit(self) -> None:
        try:
            amount = int(self.amount_var.get())
            if self.from_combo.get() == self.to_combo.get():
                raise ValueError("Source and destination branch must differ.")
            self.repo.transfer_stock(self.medicine_combo.get(), self.from_combo.get(),
                                      self.to_combo.get(), amount)
            self.set_status(
                f"Transferred {amount} of {self.medicine_combo.get()} from "
                f"{self.from_combo.get()} to {self.to_combo.get()}.", ok=True
            )
            self.amount_var.set("")
        except (ValueError, DomainError) as exc:
            self.set_status(f"Rejected: {exc}", ok=False)


# ---------------------------------------------------------------------------
# Low Stock Report (FR11)
# ---------------------------------------------------------------------------

class LowStockFrame(BaseScreen):
    TITLE = "Low Stock Report"

    def __init__(self, parent, app: PharmacyApp):
        super().__init__(parent, app)
        form = self.body

        top_row = ttk.Frame(form)
        top_row.pack(fill="x", pady=(0, 8))
        ttk.Label(top_row, text="Branch").pack(side="left")
        self.branch_combo = ttk.Combobox(top_row, state="readonly", width=20)
        self.branch_combo.pack(side="left", padx=8)
        ttk.Button(top_row, text="Refresh", command=self.on_refresh_report).pack(side="left")

        self.tree = ttk.Treeview(
            form, columns=("medicine", "name", "quantity", "reorder"), show="headings", height=10
        )
        for col, text in [("medicine", "Code"), ("name", "Name"),
                           ("quantity", "Quantity"), ("reorder", "Reorder Level")]:
            self.tree.heading(col, text=text)
        self.tree.pack(fill="both", expand=True)

    def refresh(self) -> None:
        self.branch_combo["values"] = self.branch_codes()

    def on_refresh_report(self) -> None:
        for row_id in self.tree.get_children():
            self.tree.delete(row_id)
        branch_code = self.branch_combo.get()
        if not branch_code:
            self.set_status("Select a branch first.", ok=False)
            return
        low = self.repo.list_low_stock(branch_code)
        for medicine, qty in low:
            self.tree.insert("", "end", values=(medicine.code, medicine.name, qty, medicine.reorder_level))
        self.set_status(f"{len(low)} medicine(s) at or below reorder level at {branch_code}.", ok=True)


if __name__ == "__main__":
    repository = InventoryRepository("pharmacy.db")
    app = PharmacyApp(repository)
    app.protocol("WM_DELETE_WINDOW", lambda: (repository.close(), app.destroy()))
    app.mainloop()
