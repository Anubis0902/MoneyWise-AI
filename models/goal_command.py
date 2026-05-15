"""
models/goal_command.py

Pydantic schema for natural-language goal commands.
Parsed by template2 in prompts/goal_prompt.py.
"""

from typing import Optional
from datetime import date
from pydantic import BaseModel, Field
from langchain_core.output_parsers import PydanticOutputParser


class Goalcommand(BaseModel):

    Operation: Optional[str] = Field(
        default=None,
        description="""
Type of action user wants to perform on a goal.

Allowed values: Create | Update | Delete | Fetch
""",
    )

    Title: Optional[str] = Field(
        default=None,
        description="""
Short clear name of the financial goal.

Examples:
buy shoes worth 2000 by aug -> Buy Shoes
save for iphone 15          -> Buy iPhone 15
trip to Goa next year       -> Goa Trip
build emergency fund 50000  -> Emergency Fund
""",
    )

    Started_at: Optional[date] = Field(
        default=None,
        description="""
Starting date of the goal in YYYY-MM-DD format.

Rules:
- If creating a goal and no start date mentioned, use today's date.
- For Update/Delete/Fetch with no date -> null.
""",
    )

    Deadline: Optional[date] = Field(
        default=None,
        description="""
Final target date / deadline in YYYY-MM-DD format.

Rules:
- Convert natural language to exact valid date.
- Use last reasonable date of that period.
- If not mentioned -> null.

Examples:
August 2026    -> 2026-08-31
31 Dec 2026    -> 2026-12-31
next March     -> 2027-03-31
within 6 months -> calculated future date
""",
    )

    Target_Amount: Optional[int] = Field(
        default=None,
        description="""
Total money required to complete the goal.

Examples:
buy shoes worth 2000      -> 2000
save 50000 emergency fund -> 50000
iphone goal of 80000      -> 80000
""",
    )

    Saved_Amount: Optional[int] = Field(
        default=0,
        description="""
Amount already saved or newly added toward the goal.

For create operations: default is 0.
""",
    )

    Status: Optional[str] = Field(
        default=None,
        description="""
Current status of the goal.

Allowed values: Active | Completed | Failed | Paused

Rules:
- Newly created goals → Active
- If Saved_Amount >= Target_Amount → Completed
""",
    )

    field: Optional[str] = Field(
        default=None,
        description="""
Name of the Goals table column to update.

Allowed values: Title | Started_at | Deadline | Target_Amount | Saved_Amount | Status
""",
    )

    new_value: Optional[str] = Field(
        default=None,
        description="""
New value to replace the old value in the selected field.

Rules:
- Target_Amount / Saved_Amount → numeric only
- Deadline / Started_at        → YYYY-MM-DD
- Status                       → Active / Completed / Paused / Failed
- Title                        → short meaningful title
""",
    )


# Shared parser instance used by goal_prompt.py
parser2 = PydanticOutputParser(pydantic_object=Goalcommand)
