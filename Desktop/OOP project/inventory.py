"""
Member 3 - Inventory and stock management.

This facade exposes branch-specific stock operations from InventoryRepository.
"""

from domain import StockEntry
from repository import InventoryRepository


class Inventory(InventoryRepository):
    """Branch inventory operations for receive, query and transfer flows."""

    def receive(self, medicine_code: str, branch_code: str, amount: int) -> StockEntry:
        return self.receive_stock(medicine_code, branch_code, amount)

    def quantity(self, medicine_code: str, branch_code: str) -> StockEntry:
        return self.get_stock(medicine_code, branch_code)


__all__ = ["Inventory", "StockEntry"]
