### 1. The SQLAlchemy Model (The Blueprint)

You will create a new file for this model to keep your code organized. This model defines the structure of the `chat_history` table in the database.

**File: `api/models/chat_history.py`**
```python
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, func, JSON, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column
from api.db.database import Base

# This is a class-based "blueprint" for a tenant-specific table.
# Notice there is NO __table_args__ defining a schema. It is schema-agnostic.
class ChatHistory(Base):
    """
    Represents a single question-and-answer interaction in a tenant's workspace.
    This model is a schema-agnostic blueprint.
    """
    __tablename__ = "chat_history"

    # Define the columns based on your table structure
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    citation: Mapped[dict] = mapped_column(JSON, nullable=True)
    latency: Mapped[int] = mapped_column(Integer, nullable=True)
    token_prompt: Mapped[int] = mapped_column(Integer, nullable=True)
    token_completion: Mapped[int] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

```

**Key Points:**

*   **Class-Based:** This is a standard Python class, `ChatHistory`, not a function.
*   **Inherits from `Base`:** This is what makes it a SQLAlchemy model.
*   **`__tablename__`:** This sets the name of the table in the database.
*   **No Schema:** Crucially, there is no `__table_args__ = {"schema": ...}`. This makes it a "blueprint" that can be used to create a `chat_history` table inside *any* tenant's schema.

---

### 2. The Pydantic Schema (The API Contract)

Next, you define the Pydantic schemas. These define the shape of the data when it's sent to or from your API.

**File: `api/schemas/chat_history.py`**
```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Any

# --- Schema for Reading Data ---
# This defines the shape of a chat history record when you send it from your API.
class ChatHistoryRead(BaseModel):
    id: str
    question: str
    answer: str
    citation: Optional[dict] = None
    latency: Optional[int] = None
    token_prompt: Optional[int] = None
    token_completion: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    # This config allows Pydantic to create this schema directly from
    # the SQLAlchemy ChatHistory model object.
    model_config = {
        "from_attributes": True
    }


# --- Schema for Creating Data ---
# This defines the shape of the data your API expects when a client
# wants to create a new chat history record.
class ChatHistoryCreate(BaseModel):
    question: str = Field(..., min_length=1)
    answer: str = Field(..., min_length=1)
    citation: Optional[dict] = None
    latency: Optional[int] = None
    token_prompt: Optional[int] = None
    token_completion: Optional[int] = None

```

### How This New Table Gets Created Automatically

Now that you have defined the `ChatHistory` model, you don't need to do much else. The system you've already built will handle it:

1.  **Onboarding:** When your `OnboardingService` runs, its `get_tenant_models()` method will now automatically discover this new `ChatHistory` model (because it doesn't have a `public` schema). It will then be included in the list of tables to be created for every new tenant.
2.  **Syncing:** When you run your `/admin/sync-tenants` endpoint, it will also discover the `ChatHistory` model. It will check every existing tenant's schema, and if any of them are missing the `chat_history` table, it will create it for them.

This pattern is powerful and scalable. For every new tenant-specific table you need, you simply define its class-based model "blueprint" and its Pydantic schemas, and the existing onboarding and sync logic will do the rest.


### The "Golden Rule": How the System Decides

The system makes its decision based on one line of code in your SQLAlchemy models:

1.  **If a model has `__table_args__ = {"schema": "public"}`:** It is a **GLOBAL** table. It will only be created once in the `public` schema when the application starts.
    *   *Examples: `Organization`, `OTP`*

2.  **If a model has NO `__table_args__` for the schema:** It is a **TENANT-SPECIFIC** table. It is a "blueprint" that will be used to create a new, separate table inside *every* tenant's private schema.
    *   *Examples: `User`, `ChatHistory`, `Category`*

Your application code will use this rule to automatically manage table creation.
