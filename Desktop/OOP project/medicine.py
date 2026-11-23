"""
Member 1 - OOP domain models and UML.

Medicines and their polymorphic dispensing behavior are implemented in
domain.py. This module provides the member-scoped public import surface.
"""

from domain import (
    ControlledMedicine,
    Medicine,
    OrdinaryMedicine,
)

__all__ = ["Medicine", "OrdinaryMedicine", "ControlledMedicine"]
