from pydantic import BaseModel

from app.schemas.domain import Candidate, Product, SupportTicket

SCHEMA_REGISTRY: dict[str, type[BaseModel]] = {
    "candidate": Candidate,
    "support_ticket": SupportTicket,
    "product": Product,
}


def get_schema(name: str) -> type[BaseModel]:
    try:
        return SCHEMA_REGISTRY[name]
    except KeyError as exc:
        raise ValueError(f"Unknown schema: {name}") from exc
