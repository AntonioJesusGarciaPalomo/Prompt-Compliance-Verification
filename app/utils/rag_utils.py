"""
Utility functions for RAG and JSON processing.
"""
import re
import json
import logging

logger = logging.getLogger(__name__)

def clean_and_fix_json(text: str) -> dict:
    """
    Clean and fix a JSON string that may have formatting issues.
    
    Args:
        text: The JSON string to clean and fix
        
    Returns:
        Parsed JSON dictionary
    """
    # Remove markdown code blocks if present
    cleaned_text = text
    
    if "```json" in cleaned_text:
        cleaned_text = cleaned_text.replace("```json", "").replace("```", "")
    elif "```" in cleaned_text:
        cleaned_text = cleaned_text.replace("```", "")
    
    # Try to parse the JSON directly
    try:
        return json.loads(cleaned_text)
    except json.JSONDecodeError:
        # If that fails, try to fix common issues
        try:
            fixed_json = fix_common_json_issues(cleaned_text)
            return json.loads(fixed_json)
        except json.JSONDecodeError:
            # If that still fails, try to extract fields with regex
            try:
                return extract_json_with_regex(cleaned_text)
            except Exception as e:
                logger.error(f"Failed to parse JSON: {e}")
                return {
                    "status": "UNCERTAIN",
                    "compliance_score": 5.0,
                    "issues": [],
                    "relevant_policies": []
                }

def fix_common_json_issues(text: str) -> str:
    """
    Fix common JSON formatting issues.
    
    Args:
        text: The JSON string to fix
        
    Returns:
        Fixed JSON string
    """
    # Remove trailing commas before closing brackets
    text = re.sub(r',\s*}', '}', text)
    text = re.sub(r',\s*]', ']', text)
    
    # Fix missing quotes around keys
    text = re.sub(r'(\s*)(\w+)(\s*):(\s*)', r'\1"\2"\3:\4', text)
    
    # Fix single quotes used instead of double quotes
    text = re.sub(r"'([^']*)'(\s*:)", r'"\1"\2', text)  # for keys
    text = re.sub(r':\s*\'([^\']*)\'([,}])', r': "\1"\2', text)  # for values
    
    return text

def extract_json_with_regex(text: str) -> dict:
    """
    Extract JSON fields using regex when JSON parsing fails.
    
    Args:
        text: The text to extract JSON from
        
    Returns:
        Extracted JSON dictionary
    """
    result = {
        "status": "UNCERTAIN",
        "compliance_score": 5.0,
        "issues": [],
        "relevant_policies": []
    }
    
    # Extract status
    status_match = re.search(r'"status"\s*:\s*"([^"]*)"', text)
    if status_match:
        status = status_match.group(1)
        if status in ["COMPLIANT", "NON_COMPLIANT", "UNCERTAIN"]:
            result["status"] = status
    
    # Extract compliance score
    score_match = re.search(r'"compliance_score"\s*:\s*(\d+(?:\.\d+)?)', text)
    if score_match:
        try:
            result["compliance_score"] = float(score_match.group(1))
        except ValueError:
            pass
    
    # Extract issues as best as we can
    issues_section = re.search(r'"issues"\s*:\s*\[(.*?)\]', text, re.DOTALL)
    if issues_section:
        issues_text = issues_section.group(1)
        issue_matches = re.finditer(r'{(.*?)}', issues_text, re.DOTALL)
        
        for issue_match in issue_matches:
            issue_text = issue_match.group(1)
            
            policy_text = ""
            policy_match = re.search(r'"policy_text"\s*:\s*"([^"]*)"', issue_text)
            if policy_match:
                policy_text = policy_match.group(1)
            
            prompt_text = ""
            prompt_match = re.search(r'"prompt_text"\s*:\s*"([^"]*)"', issue_text)
            if prompt_match:
                prompt_text = prompt_match.group(1)
            
            severity = 5.0
            severity_match = re.search(r'"severity"\s*:\s*(\d+(?:\.\d+)?)', issue_text)
            if severity_match:
                try:
                    severity = float(severity_match.group(1))
                except ValueError:
                    pass
            
            explanation = ""
            explanation_match = re.search(r'"explanation"\s*:\s*"([^"]*)"', issue_text)
            if explanation_match:
                explanation = explanation_match.group(1)
            
            if policy_text or prompt_text or explanation:
                result["issues"].append({
                    "policy_text": policy_text,
                    "prompt_text": prompt_text,
                    "severity": severity,
                    "explanation": explanation
                })
    
    # Extract relevant policies
    policies_section = re.search(r'"relevant_policies"\s*:\s*\[(.*?)\]', text, re.DOTALL)
    if policies_section:
        policies_text = policies_section.group(1)
        policy_matches = re.findall(r'"([^"]*)"', policies_text)
        result["relevant_policies"] = policy_matches
    
    return result