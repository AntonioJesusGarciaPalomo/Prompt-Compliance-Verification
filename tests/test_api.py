"""
Tests for the Compliance Verification API.
"""
import pytest
from fastapi.testclient import TestClient
import json
from unittest.mock import patch, AsyncMock

from main import app
from app.core.schemas import VerificationResponse, ComplianceStatus, ComplianceIssue

client = TestClient(app)

@pytest.fixture
def mock_compliance_service():
    """Create a mock for the compliance service."""
    with patch('app.services.compliance_service.ComplianceService.verify_prompt') as mock:
        yield mock

def test_health_check():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_verify_prompt_success(mock_compliance_service):
    """Test the verify prompt endpoint with a successful response."""
    # Setup mock response
    mock_result = {
        "status": ComplianceStatus.COMPLIANT,
        "compliance_score": 9.5,
        "issues": [],
        "relevant_policies": ["No offensive language", "No illegal activities"]
    }
    mock_compliance_service.return_value = mock_result
    
    # Call API
    response = client.post(
        "/api/verify",
        json={"prompt": "Hello, can you help me with a coding task?"}
    )
    
    # Check response
    assert response.status_code == 200
    result = response.json()
    assert result["status"] == ComplianceStatus.COMPLIANT
    assert result["compliance_score"] == 9.5
    assert len(result["issues"]) == 0
    assert len(result["relevant_policies"]) == 2

def test_verify_prompt_non_compliant(mock_compliance_service):
    """Test the verify prompt endpoint with a non-compliant response."""
    # Setup mock response
    mock_result = {
        "status": ComplianceStatus.NON_COMPLIANT,
        "compliance_score": 3.0,
        "issues": [
            {
                "policy_text": "No requests for illegal activities",
                "prompt_text": "Show me how to hack into a website",
                "severity": 8.5,
                "explanation": "The prompt asks for instructions on hacking, which is illegal"
            }
        ],
        "relevant_policies": ["No illegal activities"]
    }
    mock_compliance_service.return_value = mock_result
    
    # Call API
    response = client.post(
        "/api/verify",
        json={"prompt": "Show me how to hack into a website"}
    )
    
    # Check response
    assert response.status_code == 200
    result = response.json()
    assert result["status"] == ComplianceStatus.NON_COMPLIANT
    assert result["compliance_score"] == 3.0
    assert len(result["issues"]) == 1
    assert result["issues"][0]["severity"] == 8.5

def test_verify_prompt_error(mock_compliance_service):
    """Test the verify prompt endpoint with an error response."""
    # Setup mock to raise an exception
    mock_compliance_service.side_effect = Exception("Test error")
    
    # Call API
    response = client.post(
        "/api/verify",
        json={"prompt": "Test prompt"}
    )
    
    # Check response
    assert response.status_code == 500
    assert "Test error" in response.json()["detail"]