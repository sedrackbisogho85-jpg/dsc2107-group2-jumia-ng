"""
Member 4 - Prescription dispensing and transactions.

Atomic validation and rollback remain implemented in InventoryRepository.
"""

from repository import InventoryRepository


class DispensingService(InventoryRepository):
    """Member 4 service for pending, controlled and atomic dispense flows."""

    def dispense_prescription(self, prescription_id: int):
        return self.dispense(prescription_id)


__all__ = ["DispensingService"]
