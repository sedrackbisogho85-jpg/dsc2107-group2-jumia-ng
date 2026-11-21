"""
domain.py
---------
The OOP domain model for the Campus Pharmacy Inventory, Dispensing and
Reporting System.

Design rule (see Milestone 1, section 5): nothing in this file imports
sqlite3 or tkinter. These classes hold state and enforce the business
rules (invariants) themselves, through properties and methods. This lets
them be unit-tested with plain Python, with no database and no GUI.

Persistence is the job of repository.py. The GUI is the job of the
Tkinter screens in Milestone 3.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------
# Using specific exception types (instead of plain ValueError everywhere)
# makes it easy for the GUI layer to catch exactly the failure it expects
# and show a precise message to the user.

class DomainError(Exception):
    """Base class for every rule violation raised by the domain layer."""


class InsufficientStockError(DomainError):
    """Raised when a dispense or transfer would take stock below zero."""


class UnauthorisedPrescriberError(DomainError):
    """Raised when a controlled medicine is dispensed by a non-allow-listed prescriber."""


class InvalidPrescriptionStateError(DomainError):
    """Raised when an operation is attempted on a prescription in the wrong status."""


class EmptyPrescriptionError(DomainError):
    """Raised when a prescription with no lines is dispensed."""


# ---------------------------------------------------------------------------
# Medicine hierarchy (inheritance + polymorphism)
# ---------------------------------------------------------------------------

class Medicine(ABC):
    """
    Abstract base class for every medicine in the formulary.

    Encapsulation: the real values live in single-underscore attributes
    and are only reachable through the properties below, each of which
    validates before accepting a new value. This is what stops, e.g.,
    `medicine.unit_price = -5` from silently corrupting data.
    """

    def __init__(self, code: str, name: str, unit_price: float, reorder_level: int):
        if not code:
            raise ValueError("Medicine code cannot be empty.")
        if not name:
            raise ValueError("Medicine name cannot be empty.")

        self._code = code
        self._name = name
        self.unit_price = unit_price          # goes through the setter below
        self.reorder_level = reorder_level     # goes through the setter below

    # -- read-only identity ------------------------------------------------
    @property
    def code(self) -> str:
        return self._code

    @property
    def name(self) -> str:
        return self._name

    # -- validated, mutable attributes --------------------------------------
    @property
    def unit_price(self) -> float:
        return self._unit_price

    @unit_price.setter
    def unit_price(self, value: float) -> None:
        if value is None or value <= 0:
            raise ValueError(f"Unit price must be > 0 (got {value!r}).")
        self._unit_price = float(value)

    @property
    def reorder_level(self) -> int:
        return self._reorder_level

    @reorder_level.setter
    def reorder_level(self, value: int) -> None:
        if value is None or value < 0:
            raise ValueError(f"Reorder level must be >= 0 (got {value!r}).")
        self._reorder_level = int(value)

    # -- behaviour shared by every medicine ----------------------------------
    def is_low_stock(self, quantity: int) -> bool:
        """True when `quantity` at some branch is at or below the reorder level."""
        return quantity <= self._reorder_level

    # -- behaviour that differs per subclass (polymorphism) ------------------
    @abstractmethod
    def medicine_type(self) -> str:
        """Returns the string stored in the medicines.medicine_type column."""
        raise NotImplementedError

    @abstractmethod
    def can_dispense(self, prescriber_code: str, allow_list: "AllowList") -> bool:
        """
        Whether this medicine may be dispensed to the given prescriber.

        This is the single polymorphic decision point in the whole project:
        Prescription.dispense() calls this method on whatever subclass the
        line's medicine happens to be, without ever checking its type.
        """
        raise NotImplementedError

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(code={self._code!r}, name={self._name!r})"


class OrdinaryMedicine(Medicine):
    """A medicine with no prescriber restriction."""

    def medicine_type(self) -> str:
        return "ordinary"

    def can_dispense(self, prescriber_code: str, allow_list: "AllowList") -> bool:
        # Ordinary medicines never need an authorisation check.
        return True


class ControlledMedicine(Medicine):
    """A medicine that may only be dispensed by an allow-listed prescriber."""

    def medicine_type(self) -> str:
        return "controlled"

    def can_dispense(self, prescriber_code: str, allow_list: "AllowList") -> bool:
        return allow_list.is_authorised(prescriber_code)


# ---------------------------------------------------------------------------
# Branch
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Branch:
    """A pharmacy branch. Immutable value object: identity is its code."""
    code: str
    name: str

    def __post_init__(self):
        if not self.code:
            raise ValueError("Branch code cannot be empty.")
        if not self.name:
            raise ValueError("Branch name cannot be empty.")


# ---------------------------------------------------------------------------
# StockEntry
# ---------------------------------------------------------------------------

class StockEntry:
    """
    The quantity of ONE medicine held at ONE branch.

    This is the class that enforces "stock must never become negative"
    in the domain layer (the SQLite CHECK constraint enforces it again,
    independently, at the database layer -- see Milestone 1, section 7).
    """

    def __init__(self, medicine_code: str, branch_code: str, quantity: int = 0):
        if quantity < 0:
            raise ValueError("Initial quantity cannot be negative.")
        self._medicine_code = medicine_code
        self._branch_code = branch_code
        self._quantity = quantity

    @property
    def medicine_code(self) -> str:
        return self._medicine_code

    @property
    def branch_code(self) -> str:
        return self._branch_code

    @property
    def quantity(self) -> int:
        return self._quantity

    def receive(self, amount: int) -> None:
        """Stock arriving at the branch."""
        if amount <= 0:
            raise ValueError("Amount received must be > 0.")
        self._quantity += amount

    def reduce(self, amount: int) -> None:
        """Stock leaving the branch (dispensed or transferred out)."""
        if amount <= 0:
            raise ValueError("Amount reduced must be > 0.")
        if amount > self._quantity:
            raise InsufficientStockError(
                f"Cannot reduce stock of {self._medicine_code} at "
                f"{self._branch_code} by {amount}: only {self._quantity} available."
            )
        self._quantity -= amount

    def __repr__(self) -> str:
        return (f"StockEntry(medicine_code={self._medicine_code!r}, "
                f"branch_code={self._branch_code!r}, quantity={self._quantity})")


# ---------------------------------------------------------------------------
# Prescription and its lines
# ---------------------------------------------------------------------------

class PrescriptionStatus(Enum):
    PENDING = "pending"
    DISPENSED = "dispensed"
    CANCELLED = "cancelled"


@dataclass
class PrescriptionLine:
    """One medicine + quantity on a prescription. A simple value object."""
    medicine_code: str
    quantity: int

    def __post_init__(self):
        if self.quantity <= 0:
            raise ValueError("Prescription line quantity must be > 0.")


class Prescription:
    """
    A prescription: a fictional patient, a branch, a prescriber, one or
    more lines, and a status that only ever moves forward
    (pending -> dispensed) or sideways-and-stops (pending -> cancelled).

    `dispense()` does NOT touch the database itself -- it only applies the
    domain rules and raises on the first violation it finds. The actual
    atomic SQLite transaction lives in InventoryRepository.dispense(),
    which calls this method's checks before writing anything.
    """

    def __init__(self, patient_id: str, branch_code: str, prescriber_code: str,
                 prescription_id: Optional[int] = None):
        if not patient_id:
            raise ValueError("patient_id cannot be empty.")
        self._id = prescription_id
        self._patient_id = patient_id
        self._branch_code = branch_code
        self._prescriber_code = prescriber_code
        self._status = PrescriptionStatus.PENDING
        self._lines: list[PrescriptionLine] = []

    # -- identity / read-only ------------------------------------------------
    @property
    def id(self) -> Optional[int]:
        return self._id

    @id.setter
    def id(self, value: int) -> None:
        # Set once, by the repository, after the row has been INSERTed
        # and SQLite has assigned the AUTOINCREMENT id.
        if self._id is not None:
            raise InvalidPrescriptionStateError("Prescription id is already set.")
        self._id = value

    @property
    def patient_id(self) -> str:
        return self._patient_id

    @property
    def branch_code(self) -> str:
        return self._branch_code

    @property
    def prescriber_code(self) -> str:
        return self._prescriber_code

    @property
    def status(self) -> PrescriptionStatus:
        return self._status

    @property
    def lines(self) -> tuple[PrescriptionLine, ...]:
        return tuple(self._lines)  # read-only view; callers cannot mutate the list directly

    # -- behaviour -------------------------------------------------------
    def add_line(self, medicine_code: str, quantity: int) -> None:
        if self._status is not PrescriptionStatus.PENDING:
            raise InvalidPrescriptionStateError(
                "Cannot add a line to a prescription that is not pending."
            )
        self._lines.append(PrescriptionLine(medicine_code, quantity))

    def check_can_dispense(self, medicines: dict[str, Medicine], allow_list: "AllowList") -> None:
        """
        Runs every domain-level check for dispensing, WITHOUT changing any
        state. Raises the first violation found. The repository calls this
        before it starts the SQLite transaction, and again (defensively)
        inside it, so no check is ever skipped.

        `medicines` maps medicine_code -> Medicine instance (loaded by the
        repository), so this method never touches SQLite itself.
        """
        if self._status is not PrescriptionStatus.PENDING:
            raise InvalidPrescriptionStateError(
                f"Prescription {self._id} is {self._status.value}, not pending."
            )
        if not self._lines:
            raise EmptyPrescriptionError(f"Prescription {self._id} has no lines.")

        for line in self._lines:
            medicine = medicines[line.medicine_code]
            if not medicine.can_dispense(self._prescriber_code, allow_list):
                raise UnauthorisedPrescriberError(
                    f"Prescriber {self._prescriber_code!r} is not authorised to "
                    f"dispense controlled medicine {medicine.code!r}."
                )

    def mark_dispensed(self) -> None:
        """Called by the repository only after every stock reduction has succeeded."""
        if self._status is not PrescriptionStatus.PENDING:
            raise InvalidPrescriptionStateError("Only a pending prescription can be dispensed.")
        self._status = PrescriptionStatus.DISPENSED

    def cancel(self) -> None:
        if self._status is not PrescriptionStatus.PENDING:
            raise InvalidPrescriptionStateError("Only a pending prescription can be cancelled.")
        self._status = PrescriptionStatus.CANCELLED

    def __repr__(self) -> str:
        return (f"Prescription(id={self._id}, patient_id={self._patient_id!r}, "
                f"status={self._status.value}, lines={len(self._lines)})")


# ---------------------------------------------------------------------------
# AllowList
# ---------------------------------------------------------------------------

class AllowList:
    """
    The simulated list of prescribers authorised to prescribe controlled
    medicines. Backed in the database by the allowed_prescribers table,
    but the domain layer only ever sees this plain, testable wrapper.
    """

    def __init__(self, authorised_prescribers: Optional[set[str]] = None):
        self._authorised = set(authorised_prescribers or ())

    def is_authorised(self, prescriber_code: str) -> bool:
        return prescriber_code in self._authorised

    def add(self, prescriber_code: str) -> None:
        if not prescriber_code:
            raise ValueError("prescriber_code cannot be empty.")
        self._authorised.add(prescriber_code)

    def remove(self, prescriber_code: str) -> None:
        self._authorised.discard(prescriber_code)

    def __iter__(self):
        return iter(sorted(self._authorised))

    def __repr__(self) -> str:
        return f"AllowList({sorted(self._authorised)!r})"
