"""
Member 6 - Reporting and low-stock integration.

Low-stock is implemented as quantity <= medicine reorder_level.
"""

from domain import Medicine
from repository import InventoryRepository


class ReportService(InventoryRepository):
    def low_stock(self, branch_code: str) -> list[tuple[Medicine, int]]:
        return self.list_low_stock(branch_code)


__all__ = ["ReportService"]
