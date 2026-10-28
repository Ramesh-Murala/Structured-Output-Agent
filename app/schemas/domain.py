from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl


class StrictOutputModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Candidate(StrictOutputModel):
    name: Annotated[str, Field(min_length=1, max_length=120)]
    email: EmailStr
    skills: Annotated[list[str], Field(min_length=1)]
    years_experience: Annotated[float, Field(ge=0, le=60)]


class SupportTicket(StrictOutputModel):
    category: Literal["billing", "technical", "account", "feature_request", "other"]
    priority: Literal["low", "medium", "high", "critical"]
    summary: Annotated[str, Field(min_length=5, max_length=300)]
    requires_human: bool
    sentiment: Literal["negative", "neutral", "positive"]


class Product(StrictOutputModel):
    name: Annotated[str, Field(min_length=1, max_length=160)]
    price: Annotated[float, Field(gt=0, allow_inf_nan=False)]
    currency: Annotated[str, Field(pattern=r"^[A-Z]{3}$")]
    in_stock: bool
    product_url: HttpUrl | None = None
