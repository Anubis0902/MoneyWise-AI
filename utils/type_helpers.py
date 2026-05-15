"""
utils/type_helpers.py

Category sets and helper to infer transaction Type from Category.
Used by transaction_service.py.
"""

INCOME_CATS: set[str] = {
    "Salary",
    "Pocket Money",
    "Freelancing",
    "Business",
    "Gift",
    "Refund",
    "Cashback",
    "Investment",
    "Other",
}

EXPENSE_CATS: set[str] = {
    "Food",
    "Groceries",
    "Transport",
    "Education",
    "Shopping",
    "Entertainment",
    "Healthcare",
    "Bills",
    "Travel",
    "Subscription",
    "Investment",
    "Shares",
    "Stationery",
    "Other",
}


def _infer_type(Type: str | None, Category: str | None) -> str | None:
    """
    Resolve transaction Type from explicit value or from Category.

    Priority:
      1. If Type is explicitly provided, use it.
      2. If Category belongs to INCOME_CATS  → "Income"
      3. If Category belongs to EXPENSE_CATS → "Expense"
      4. Otherwise return None (caller should handle the error).
    """
    if Type is not None:
        return Type
    if Category in INCOME_CATS:
        return "Income"
    if Category in EXPENSE_CATS:
        return "Expense"
    return None
