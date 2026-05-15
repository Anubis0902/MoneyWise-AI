"""
utils/formatters.py

Centralized formatting utilities for the MoneyWise application.
Implements Indian Number System (Lakhs/Crores) and comma grouping.
"""

def format_indian_currency(amount: float, include_symbol: bool = True) -> str:
    """
    Formats a number into Indian currency style (e.g., 1,00,000).
    Also handles shorthand for large numbers (L/Cr) if needed.
    """
    if amount is None:
        return "₹0" if include_symbol else "0"
        
    s = f"{float(amount):.0f}"
    res = ""
    if len(s) > 3:
        last_three = s[-3:]
        remaining = s[:-3]
        res = "," + last_three
        while len(remaining) > 2:
            res = "," + remaining[-2:] + res
            remaining = remaining[:-2]
        res = remaining + res
    else:
        res = s
        
    return f"₹{res}" if include_symbol else res

def format_indian_shorthand(amount: float) -> str:
    """
    Converts large numbers to Indian shorthand (e.g., 1.5L, 2Cr).
    """
    if amount is None:
        return "₹0"
    
    abs_amt = abs(amount)
    if abs_amt >= 10000000: # 1 Crore
        return f"₹{amount/10000000:.2f}Cr"
    elif abs_amt >= 100000: # 1 Lakh
        return f"₹{amount/100000:.2f}L"
    else:
        return format_indian_currency(amount)
