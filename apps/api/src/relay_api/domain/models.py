"""Strict boundaries for customer inputs, model suggestions and enterprise data."""

from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Login(Strict):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=200)


class Chat(Strict):
    message: str = Field(min_length=1, max_length=2000)
    accountId: str | None = Field(default=None, pattern=r"^ACC-\d{4}$")


class Confirmation(Strict):
    actionId: str = Field(pattern=r"^ACT-[a-f0-9]{32}$")
    confirm: bool


class Interpretation(Strict):
    intent: Literal["account", "billing", "network", "legacy", "case", "unknown", "handoff"]
    service: Literal["home-internet", "mobile", "unknown"]
    confidence: float = Field(ge=0, le=1)


class Selection(Strict):
    fact_ids: list[int] = Field(max_length=20)


class Enterprise(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)


class Auth(Enterprise):
    accessToken: str = Field(min_length=1)
    customerId: str = Field(pattern=r"^(CUST|AGENT)-\d+$")
    accountId: str | None = None
    roles: list[Literal["customer", "support-agent"]]
    expiresIn: int = Field(ge=0, le=86400)


class Profile(Enterprise):
    name: str = ""
    customerId: str
    accountId: str | None = None
    postalCode: str = Field(pattern=r"^\d{5}$")


class Plan(Enterprise):
    name: str = Field(min_length=1, max_length=100)
    monthlyPrice: float = Field(ge=0)


class Service(Enterprise):
    serviceId: str = Field(pattern=r"^SVC-\d+$")
    type: Literal["home-internet", "mobile"]
    status: str


class Account(Enterprise):
    accountId: str
    customerId: str
    status: str
    plan: Plan
    services: list[Service] = Field(min_length=1)


class Item(Enterprise):
    description: str
    amount: float


class Billing(Enterprise):
    accountId: str
    period: str
    total: float = Field(ge=0)
    items: list[Item]


class Outage(Enterprise):
    postalCode: str
    status: Literal["normal", "degraded", "outage", "unknown"]
    incidentId: str | None = None
    estimatedRestoration: str | None = None


class Diagnostic(Enterprise):
    diagnosticId: str = Field(pattern=r"^DIAG-[A-F0-9]+$")
    serviceId: str
    result: Literal["no_device_fault_detected"]


class Case(Enterprise):
    caseId: str = Field(pattern=r"^CASE-[A-F0-9]+$")
    status: Literal["open"]
    accountId: str
    customerId: str
    idempotencyKey: str
