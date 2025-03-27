#!/usr/bin/env python3
"""
Client script for interacting with the Prompt Compliance Verification API.
"""
import argparse
import json
import os
import sys
import requests
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_api_url() -> str:
    """Get the API URL from environment variables or use default."""
    host = os.environ.get("API_HOST", "localhost")
    port = os.environ.get("API_PORT", "8000")
    return f"http://{host}:{port}/api"

def check_health() -> Dict[str, Any]:
    """Check if the API is healthy."""
    try:
        response = requests.get(f"{get_api_url()}/health")
        return response.json()
    except requests.RequestException as e:
        return {"status": "error", "message": str(e)}

def verify_prompt(prompt: str) -> Dict[str, Any]:
    """Verify if a prompt complies with policies."""
    try:
        response = requests.post(
            f"{get_api_url()}/verify",
            json={"prompt": prompt}
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return {"status": "UNCERTAIN", "error": str(e), "compliance_score": 0.0, "issues": [], "relevant_policies": []}

def add_policy_text(policy_text: str, policy_name: Optional[str] = None) -> Dict[str, Any]:
    """Add policy text to the system."""
    payload = {"policy_text": policy_text}
    if policy_name:
        payload["policy_name"] = policy_name
    
    try:
        response = requests.post(
            f"{get_api_url()}/policies/add-text",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return {"success": False, "message": str(e)}

def add_policy_file(file_path: str, policy_name: Optional[str] = None) -> Dict[str, Any]:
    """Add a policy file to the system."""
    if not os.path.exists(file_path):
        return {"success": False, "message": f"File not found: {file_path}"}
    
    try:
        files = {"file": (os.path.basename(file_path), open(file_path, "rb"))}
        data = {}
        if policy_name:
            data["policy_name"] = policy_name
        
        response = requests.post(
            f"{get_api_url()}/policies/add-file",
            files=files,
            data=data
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return {"success": False, "message": str(e)}

def list_policies() -> Dict[str, Any]:
    """List all policy documents."""
    try:
        response = requests.get(f"{get_api_url()}/policies/list")
        response.raise_for_status()
        return {"success": True, "policies": response.json()}
    except requests.RequestException as e:
        return {"success": False, "message": str(e)}

def clear_policies() -> Dict[str, Any]:
    """Clear all policies from the system."""
    try:
        response = requests.delete(f"{get_api_url()}/policies/clear")
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return {"success": False, "message": str(e)}

def print_verification_result(result: Dict[str, Any]) -> None:
    """Print verification result in a human-readable format."""
    print("\n=== Compliance Verification Result ===")
    print(f"Status: {result.get('status', 'UNKNOWN')}")
    print(f"Compliance Score: {result.get('compliance_score', 0.0)}/10.0")
    
    if "error" in result and result["error"]:
        print(f"\nError: {result['error']}")
    
    issues = result.get("issues", [])
    if issues:
        print(f"\nIssues Found ({len(issues)}):")
        for i, issue in enumerate(issues, 1):
            print(f"\n  Issue {i}:")
            print(f"  Severity: {issue.get('severity', 0.0)}/10.0")
            print(f"  Explanation: {issue.get('explanation', 'No explanation provided')}")
            print(f"  Policy Text: {issue.get('policy_text', 'No policy text provided')}")
            print(f"  Prompt Text: {issue.get('prompt_text', 'No prompt text provided')}")
    else:
        print("\nNo issues found.")
    
    relevant_policies = result.get("relevant_policies", [])
    if relevant_policies:
        print(f"\nRelevant Policies ({len(relevant_policies)}):")
        for i, policy in enumerate(relevant_policies, 1):
            print(f"  {i}. {policy}")
    
    print("\n=====================================")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Prompt Compliance Verification Client")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Health check command
    health_parser = subparsers.add_parser("health", help="Check API health")
    
    # Verify prompt command
    verify_parser = subparsers.add_parser("verify", help="Verify prompt compliance")
    verify_parser.add_argument("prompt", help="Prompt to verify")
    
    # Add policy text command
    add_text_parser = subparsers.add_parser("add-text", help="Add policy text")
    add_text_parser.add_argument("text", help="Policy text to add")
    add_text_parser.add_argument("--name", help="Policy name")
    
    # Add policy file command
    add_file_parser = subparsers.add_parser("add-file", help="Add policy file")
    add_file_parser.add_argument("file", help="Path to policy file")
    add_file_parser.add_argument("--name", help="Policy name")
    
    # List policies command
    list_parser = subparsers.add_parser("list", help="List policies")
    
    # Clear policies command
    clear_parser = subparsers.add_parser("clear", help="Clear all policies")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Execute command
    if args.command == "health":
        result = check_health()
        print(json.dumps(result, indent=2))
    elif args.command == "verify":
        result = verify_prompt(args.prompt)
        print_verification_result(result)
    elif args.command == "add-text":
        result = add_policy_text(args.text, args.name)
        print(json.dumps(result, indent=2))
    elif args.command == "add-file":
        result = add_policy_file(args.file, args.name)
        print(json.dumps(result, indent=2))
    elif args.command == "list":
        result = list_policies()
        print(json.dumps(result, indent=2))
    elif args.command == "clear":
        result = clear_policies()
        print(json.dumps(result, indent=2))
    else:
        parser.print_help()

if __name__ == "__main__":
    main()