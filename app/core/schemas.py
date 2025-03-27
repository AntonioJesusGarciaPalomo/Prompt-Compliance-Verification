"""Pydantic schemas for the API requests and responses."""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Literal
from enum import Enum

class ComplianceStatus(str, Enum):
    """Enum for compliance status."""
    COMPLIANT = "COMPLIANT"
    NON_COMPLIANT = "NON_COMPLIANT"
    UNCERTAIN = "UNCERTAIN"

class PromptVerificationRequest(BaseModel):
    """Request schema for prompt verification."""
    prompt: str = Field(..., description="The prompt to verify for compliance")

class PolicyTextRequest(BaseModel):
    """Request schema for adding policy text."""
    policy_text: str = Field(..., description="The policy text to add")
    policy_name: Optional[str] = Field(None, description="Optional name for the policy")

class ComplianceIssue(BaseModel):
    """Schema for a compliance issue."""
    policy_text: str = Field(..., description="The policy text that is relevant to the issue")
    prompt_text: str = Field(..., description="The prompt text that conflicts with the policy")
    severity: float = Field(..., description="A score from 0-10 indicating severity (10 being most severe)")
    explanation: str = Field(..., description="An explanation of the conflict/issue")

class VerificationResponse(BaseModel):
    """Response schema for verification results."""
    status: ComplianceStatus = Field(..., description="Compliance status")
    compliance_score: float = Field(..., description="Overall compliance score from 0-10")
    issues: List[ComplianceIssue] = Field([], description="List of detected compliance issues")
    relevant_policies: List[str] = Field([], description="List of relevant policies for this prompt")

class ApiResponse(BaseModel):
    """Generic API response schema."""
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="A message describing the result")
    data: Optional[Dict[str, Any]] = Field(None, description="Optional additional data")