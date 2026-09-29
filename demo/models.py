from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Subject(StrictModel):
    subject_id: str = Field(min_length=1, max_length=64)
    role: Literal["admin", "teacher", "student", "guest"]
    department: str = Field(default="public", max_length=64)
    courses: list[str] = Field(default_factory=list, max_length=20)
    clearance: Literal["public", "confidential", "restricted"] = "public"


class Resource(StrictModel):
    resource_id: str = Field(min_length=1, max_length=128)
    owner: str = Field(min_length=1, max_length=64)
    classification: Literal["public", "confidential", "restricted"]
    department: str = Field(default="public", max_length=64)
    course: str | None = Field(default=None, max_length=64)


class Environment(StrictModel):
    network_zone: Literal["campus", "vpn", "public"] = "public"
    hour: int = Field(default=12, ge=0, le=23)


class AccessRequest(StrictModel):
    subject: Subject
    resource: Resource
    action: Literal["read", "write", "delete", "delegate"]
    environment: Environment = Field(default_factory=Environment)
    capability: dict | None = None


class CapabilityIssueRequest(StrictModel):
    issuer: Subject
    subject_id: str = Field(min_length=1, max_length=64)
    resource: Resource
    actions: list[Literal["read", "write", "delete", "delegate"]] = Field(min_length=1, max_length=4)
    ttl_seconds: int = Field(default=300, ge=10, le=3600)
    may_delegate: bool = False


class CapabilityDelegateRequest(StrictModel):
    parent: dict
    subject_id: str = Field(min_length=1, max_length=64)
    actions: list[Literal["read", "write", "delete", "delegate"]] = Field(min_length=1, max_length=4)
    ttl_seconds: int = Field(default=120, ge=10, le=3600)
    may_delegate: bool = False


class SecurityEvent(StrictModel):
    event_id: str = Field(min_length=1, max_length=64)
    source: str = Field(min_length=1, max_length=128)
    actor: str = Field(min_length=1, max_length=64)
    action: str = Field(min_length=1, max_length=64)
    resource: str = Field(min_length=1, max_length=128)
    decision: Literal["allowed", "denied"]
    ground_truth: Literal["benign", "malicious"] = "benign"


class SignedAlert(StrictModel):
    payload: dict
    signature: str = Field(min_length=16, max_length=512)
    public_key: str = Field(min_length=16, max_length=512)


class SybilRequest(StrictModel):
    count: int = Field(default=8, ge=1, le=50)
    stake_per_identity: int = Field(default=0, ge=0, le=100)
