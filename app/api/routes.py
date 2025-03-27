"""API routes for the compliance verification service."""
from fastapi import APIRouter, HTTPException, BackgroundTasks, Request, UploadFile, File, Form
from fastapi.responses import JSONResponse
import os
import logging
import glob
from typing import List, Dict, Any, Optional, Literal
import uuid

from app.core.schemas import (
    PromptVerificationRequest, 
    VerificationResponse,
    ApiResponse,
    PolicyTextRequest
)
from app.services.compliance_service import ComplianceService
from app.core.config import settings

router = APIRouter(prefix="/api")
logger = logging.getLogger(__name__)

# Initialize service
compliance_service = ComplianceService()

@router.get("/health")
async def health_check():
    """Check if the API is healthy."""
    return {"status": "ok"}

@router.post("/verify", response_model=VerificationResponse)
async def verify_prompt(request: PromptVerificationRequest):
    """
    Verify if a prompt complies with policies.
    
    Args:
        request: The request with the prompt to verify
        
    Returns:
        Verification results
    """
    try:
        result = await compliance_service.verify_prompt(request.prompt)
        return result
    except Exception as e:
        logger.error(f"Error verifying prompt: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error verifying prompt: {str(e)}")

@router.post("/policies/add-text", response_model=ApiResponse)
async def add_policy_text(request: PolicyTextRequest):
    """
    Add policy text to the system.
    
    Args:
        request: The request with the policy text to add
        
    Returns:
        API response
    """
    try:
        success = compliance_service.add_policy_text(request.policy_text, request.policy_name)
        return ApiResponse(
            success=success,
            message="Policy text added successfully" if success else "Failed to add policy text",
            data=None
        )
    except Exception as e:
        logger.error(f"Error adding policy text: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error adding policy text: {str(e)}")

@router.post("/policies/add-file", response_model=ApiResponse)
async def add_policy_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    policy_name: Optional[str] = Form(None)
):
    """
    Add a policy file to the system.
    
    Args:
        background_tasks: FastAPI background tasks
        file: The policy file to upload
        policy_name: Optional name for the policy
        
    Returns:
        API response
    """
    try:
        # Create temporary file
        filename = f"{uuid.uuid4().hex}_{file.filename}"
        temp_file_path = os.path.join("temp", filename)
        os.makedirs("temp", exist_ok=True)
        
        with open(temp_file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Add file to policies
        success = compliance_service.add_policy_document(temp_file_path)
        
        # Clean up temp file in background
        background_tasks.add_task(os.remove, temp_file_path)
        
        return ApiResponse(
            success=success,
            message="Policy file added successfully" if success else "Failed to add policy file",
            data=None
        )
    except Exception as e:
        logger.error(f"Error adding policy file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error adding policy file: {str(e)}")

@router.get("/policies/list", response_model=List[str])
async def list_policies():
    """
    List all policy documents.
    
    Returns:
        List of policy documents
    """
    try:
        policies = compliance_service.list_policies()
        return policies
    except Exception as e:
        logger.error(f"Error listing policies: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing policies: {str(e)}")

@router.delete("/policies/clear", response_model=ApiResponse)
async def clear_policies():
    """
    Clear all policies from the system.
    
    Returns:
        API response
    """
    try:
        success = compliance_service.clear_policies()
        return ApiResponse(
            success=success,
            message="Policies cleared successfully" if success else "Failed to clear policies",
            data=None
        )
    except Exception as e:
        logger.error(f"Error clearing policies: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error clearing policies: {str(e)}")