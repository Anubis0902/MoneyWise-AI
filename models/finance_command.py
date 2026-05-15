"""
models/finance_command.py

Pydantic schema for natural-language transaction commands.
Parsed by template1 in prompts/transaction_prompt.py.
"""

from typing import Optional
from pydantic import BaseModel, Field
from langchain_core.output_parsers import PydanticOutputParser


class Financecommand(BaseModel):

    Operation: str = Field(
        description="""
Type of action user wants to perform.

Allowed values:
Add
Fetch
Update
Delete

Examples:
Bought books worth 120 -> Add
Fetch all education expenses -> Fetch
Update books purchase amount to 300 -> Update
Delete pizza expense -> Delete
"""
    )

    Title: Optional[str] = Field(
        default=None,
        description="""
Short clear transaction title.

Examples:
apple shares purchase, books purchase, hotel dinner, salary received,
pocket money, petrol refill, freelancing payment
""",
    )

    Amount: Optional[int] = Field(
        default=None,
        description="""
Final transaction amount in numeric form only.

Rules:
- If quantity × price is given, calculate total amount.
Example:
4 shares each 51 rs = 204

Examples:
120, 500, 204, 25000
""",
    )

    Category: Optional[str] = Field(
        default=None,
        description="""
Smart category field.

Use only categories from the allowed list.
Never create random/custom categories.
If no clear match, use Other.

For Expense transactions:
Food, Groceries, Transport, Education, Shopping, Entertainment,
Healthcare, Bills, Travel, Investment, Subscription, Other

For Income transactions:
Salary, Pocket Money, Freelancing, Gift, Refund, Cashback, Investment, Other

Examples:
Bought Apple shares -> Investment
Father gave me 500  -> Pocket Money
Got cashback of 50  -> Cashback
""",
    )

    Mode: Optional[str] = Field(
        default=None,
        description="""
Payment mode.

Examples: Cash, Online, UPI, Credit Card, Debit Card, Wallet.

If not mentioned -> Online
""",
    )

    Type: Optional[str] = Field(
        default=None,
        description="""
Transaction nature.

Allowed values: Expense | Income

Expense = money went out.
Income  = money came in.

CRITICAL RULE: Type is ALWAYS only "Income" or "Expense".
Category is where the sub-type goes.

WRONG: Type=Cashback  RIGHT: Type=Income,  Category=Cashback
WRONG: Type=Salary    RIGHT: Type=Income,  Category=Salary
""",
    )

    field: Optional[str] = Field(
        default=None,
        description="""
Name of the database column to update.

Allowed values: Title | Amount | Category | Mode | Type
""",
    )

    new_value: Optional[str] = Field(
        default=None,
        description="""
New value to replace the old value in the selected field.

Rules:
- Amount  → numeric only
- Mode    → Cash / Online / UPI / Credit Card / Debit Card
- Type    → Expense or Income
- Category → proper category name
- Title   → short meaningful title
""",
    )


# Shared parser instance used by transaction_prompt.py
parser = PydanticOutputParser(pydantic_object=Financecommand)
