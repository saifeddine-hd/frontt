import re
from typing import Dict, Any

def redact_secret(secret: str) -> str:
    """Redact secret by showing only first and last 4 characters"""
    if len(secret) <= 8:
        return "*" * len(secret)
    
    return f"{secret[:4]}{'*' * (len(secret) - 8)}{secret[-4:]}"

def is_in_allowlist(finding: 'Finding', allowlist: Dict[str, Any]) -> bool:
    """Check if finding should be ignored based on allowlist"""
    if not allowlist:
        return False
    
    # Check file patterns
    file_patterns = allowlist.get("files", [])
    for pattern in file_patterns:
        if re.search(pattern, finding.file_path):
            return True
    
    # Check secret patterns
    secret_patterns = allowlist.get("secrets", [])
    for pattern in secret_patterns:
        if re.search(pattern, finding.secret):
            return True
    
    # Check rule exclusions
    excluded_rules = allowlist.get("rules", [])
    if finding.rule_id in excluded_rules:
        return True
    
    return False