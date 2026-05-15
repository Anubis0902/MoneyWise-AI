"""
prompts/goal_prompt.py

PromptTemplate for extracting structured goal data
from a natural-language user message.
"""

from langchain_core.prompts import PromptTemplate
from models.goal_command import parser2

template2 = PromptTemplate(
    template="""
You are a smart financial goal extractor.

Your job is to read the user's message and convert it into structured goal data.

Extract these fields:
1. Operation
2. Title
3. Started_at
4. Deadline
5. Target_Amount
6. Saved_Amount
7. Status

Field Rules:

1. Operation

Detect what user wants to do.

Allowed values: Create | Update | Delete | Fetch

If user says:
fetch all marriage fund goals → Operation = Fetch, Title = Marriage Fund
show all bike goals           → Operation = Fetch, Title = Bike

For Update operations:
- Extract only fields user wants to change.
- Do not fill unrelated fields with defaults.
- Do not set Status unless user explicitly mentions it.
- Use Title to identify the goal.


2. Title

Create short meaningful goal title.

Examples:
buy shoes worth 2000 by aug → Buy Shoes
save for iphone 15          → Buy iPhone 15
trip to Goa next year       → Goa Trip
build emergency fund 50000  → Emergency Fund
buy gaming laptop           → Gaming Laptop


3. Started_at

Goal start date in YYYY-MM-DD format.

Rules:
- If Operation = Create and no explicit start date → today's current date.
- For Update/Delete/Fetch with no date → null.


4. Deadline

Goal completion deadline in YYYY-MM-DD format.

Relative month phrases must be converted to exact dates:
next march    → 2027-03-31
this march    → 2026-03-31
march 2027    → 2027-03-31
by August     → 2026-08-31
within 6 months → calculate future date
31 Dec 2026   → 2026-12-31

Recognize short month names:
jan=January, feb=February, mar=March, apr=April,
aug=August, sep=September, oct=October, nov=November, dec=December

Do not return text like "by August", "soon", "next month".


5. Target_Amount

Total required amount (numeric only).


6. Saved_Amount

Money already saved or newly added.
If Create and not mentioned → 0.


7. Status

Allowed values: Active | Completed | Paused | Failed

Rules:
- Newly created goals → Active
- If Saved_Amount >= Target_Amount → Completed
- User says pause/hold/stop temporarily → Paused
- User says cancel/failed/missed deadline → Failed
- If not specified, default → Active

For Update operations, also extract:
field     → column to modify: Title | Started_At | Deadline | Target_Amount | Saved_Amount | Status
new_value → replacement value

For Delete operations:
Extract the goal title or identifying phrase user wants removed.

Important Rules:
- Return only structured output.
- Do not explain anything.
- Do not return markdown.
- Use null where field is not applicable.
- Understand natural language.
- Always create best possible title.
- All dates must be in YYYY-MM-DD format only.
- If Operation = Update:
    Only changed fields should have values.
    All untouched fields must be null.

User Input: {user_query2}

{format_instructions}

Return only JSON.
""",
    input_variables=["user_query2"],
    partial_variables={
        "format_instructions": parser2.get_format_instructions()
    },
)
