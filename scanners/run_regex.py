#!/usr/bin/env python3
"""
Regex-based scanner for SecretHawk
"""

import re
import os
from typing import List, Dict, Any, Pattern

class RegexScanner:
    def __init__(self):
        self.patterns = self._load_patterns()
    
    def _load_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Load regex patterns for secret detection"""
        return {
            # AWS Keys
            "aws_access_key": {
                "pattern": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
                "severity": "critical",
                "description": "AWS Access Key ID"
            },
            "aws_secret_key": {
                "pattern": re.compile(r"\b[A-Za-z0-9/+=]{40}\b"),
                "severity": "critical",
                "description": "AWS Secret Access Key"
            },
            
            # GitHub Tokens
            "github_pat": {
                "pattern": re.compile(r"\bghp_[A-Za-z0-9]{36}\b"),
                "severity": "high",
                "description": "GitHub Personal Access Token"
            },
            "github_oauth": {
                "pattern": re.compile(r"\bgho_[A-Za-z0-9]{36}\b"),
                "severity": "high",
                "description": "GitHub OAuth Token"
            },
            "github_app": {
                "pattern": re.compile(r"\bghs_[A-Za-z0-9]{36}\b"),
                "severity": "high",
                "description": "GitHub App Token"
            },
            
            # Google Cloud
            "gcp_api_key": {
                "pattern": re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"),
                "severity": "high",
                "description": "Google API Key"
            },
            "gcp_service_account": {
                "pattern": re.compile(r'"type":\s*"service_account"'),
                "severity": "critical",
                "description": "Google Cloud Service Account Key"
            },
            
            # Stripe
            "stripe_secret_key": {
                "pattern": re.compile(r"\bsk_live_[A-Za-z0-9]{24}\b"),
                "severity": "critical",
                "description": "Stripe Live Secret Key"
            },
            "stripe_publishable_key": {
                "pattern": re.compile(r"\bpk_live_[A-Za-z0-9]{24}\b"),
                "severity": "medium",
                "description": "Stripe Live Publishable Key"
            },
            
            # Slack
            "slack_token": {
                "pattern": re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"),
                "severity": "high",
                "description": "Slack Token"
            },
            "slack_webhook": {
                "pattern": re.compile(r"hooks\.slack\.com/services/[A-Z0-9/]+"),
                "severity": "medium",
                "description": "Slack Webhook URL"
            },
            
            # JWT
            "jwt_token": {
                "pattern": re.compile(r"\beyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*\b"),
                "severity": "medium",
                "description": "JSON Web Token"
            },
            
            # Private Keys
            "rsa_private_key": {
                "pattern": re.compile(r"-----BEGIN RSA PRIVATE KEY-----"),
                "severity": "critical",
                "description": "RSA Private Key"
            },
            "openssh_private_key": {
                "pattern": re.compile(r"-----BEGIN OPENSSH PRIVATE KEY-----"),
                "severity": "critical",
                "description": "OpenSSH Private Key"
            },
            "dsa_private_key": {
                "pattern": re.compile(r"-----BEGIN DSA PRIVATE KEY-----"),
                "severity": "critical",
                "description": "DSA Private Key"
            },
            "ec_private_key": {
                "pattern": re.compile(r"-----BEGIN EC PRIVATE KEY-----"),
                "severity": "critical",
                "description": "EC Private Key"
            },
            
            # Database URLs
            "postgres_url": {
                "pattern": re.compile(r"postgresql://[^\\s'\"]*"),
                "severity": "critical",
                "description": "PostgreSQL Connection String"
            },
            "mysql_url": {
                "pattern": re.compile(r"mysql://[^\\s'\"]*"),
                "severity": "critical",
                "description": "MySQL Connection String"
            },
            "mongodb_url": {
                "pattern": re.compile(r"mongodb(\+srv)?://[^\\s'\"]*"),
                "severity": "critical",
                "description": "MongoDB Connection String"
            },
            
            # Generic Patterns
            "generic_api_key": {
                "pattern": re.compile(r"['\"]?[aA]pi[_-]?[kK]ey['\"]?\s*[:=]\s*['\"]?[A-Za-z0-9_-]{16,}['\"]?"),
                "severity": "medium",
                "description": "Generic API Key"
            },
            "generic_secret": {
                "pattern": re.compile(r"['\"]?[sS]ecret['\"]?\s*[:=]\s*['\"]?[A-Za-z0-9_-]{16,}['\"]?"),
                "severity": "medium",
                "description": "Generic Secret"
            },
            "generic_token": {
                "pattern": re.compile(r"['\"]?[tT]oken['\"]?\s*[:=]\s*['\"]?[A-Za-z0-9_-]{16,}['\"]?"),
                "severity": "medium",
                "description": "Generic Token"
            },
            
            # High-entropy strings (basic implementation)
            "high_entropy": {
                "pattern": re.compile(r"\b[A-Za-z0-9+/]{32,}={0,2}\b"),
                "severity": "low",
                "description": "High Entropy String (potential secret)"
            }
        }
    
    def scan_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Scan a single file for secrets"""
        findings = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')
                
                for rule_id, rule_config in self.patterns.items():
                    pattern = rule_config["pattern"]
                    
                    for line_no, line in enumerate(lines, 1):
                        matches = pattern.finditer(line)
                        
                        for match in matches:
                            # Skip obvious false positives
                            if self._is_false_positive(match.group(), rule_id):
                                continue
                            
                            finding = {
                                "file": file_path,
                                "line": line_no,
                                "column": match.start() + 1,
                                "type": rule_id,
                                "secret": match.group(),
                                "severity": rule_config["severity"],
                                "description": rule_config["description"],
                                "scanner": "regex"
                            }
                            findings.append(finding)
        
        except Exception as e:
            print(f"Error scanning file {file_path}: {e}")
        
        return findings
    
    def scan_directory(self, directory: str) -> List[Dict[str, Any]]:
        """Scan directory recursively"""
        findings = []
        
        for root, dirs, files in os.walk(directory):
            # Skip common directories that shouldn't be scanned
            dirs[:] = [d for d in dirs if not self._should_skip_directory(d)]
            
            for file in files:
                if self._should_scan_file(file):
                    file_path = os.path.join(root, file)
                    file_findings = self.scan_file(file_path)
                    findings.extend(file_findings)
        
        return findings
    
    def _should_skip_directory(self, dirname: str) -> bool:
        """Check if directory should be skipped"""
        skip_dirs = {
            '.git', 'node_modules', '__pycache__', '.pytest_cache',
            'vendor', 'dist', 'build', '.venv', 'venv',
            '.tox', '.coverage', '.mypy_cache'
        }
        return dirname in skip_dirs or dirname.startswith('.')
    
    def _should_scan_file(self, filename: str) -> bool:
        """Check if file should be scanned"""
        # Skip binary file extensions
        skip_extensions = {
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg',
            '.zip', '.tar', '.gz', '.rar', '.7z',
            '.exe', '.dll', '.so', '.dylib',
            '.pdf', '.doc', '.docx', '.xls', '.xlsx',
            '.mp3', '.mp4', '.avi', '.mov', '.wav',
            '.pyc', '.pyo', '.class', '.o', '.obj'
        }
        
        _, ext = os.path.splitext(filename.lower())
        return ext not in skip_extensions
    
    def _is_false_positive(self, match: str, rule_id: str) -> bool:
        """Basic false positive detection"""
        # Skip obvious placeholders and examples
        false_positive_patterns = [
            r'^(example|test|demo|placeholder|fake|dummy|sample)',
            r'^[x]{8,}$',  # All x's
            r'^[*]{8,}$',  # All asterisks
            r'^[0]{8,}$',  # All zeros
            r'^[1]{8,}$',  # All ones
            r'^(your|my|our)[-_]?(secret|key|token)',
            r'^\$\{.*\}$',  # Environment variable placeholder
            r'^<.*>$',      # XML/HTML placeholder
        ]
        
        match_lower = match.lower()
        for pattern in false_positive_patterns:
            if re.match(pattern, match_lower):
                return True
        
        # Rule-specific false positive detection
        if rule_id == "high_entropy":
            # Skip common base64 padding and short strings
            if len(match) < 20 or match.endswith('=='):
                return True
        
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python run_regex.py <directory>")
        sys.exit(1)
    
    scanner = RegexScanner()
    findings = scanner.scan_directory(sys.argv[1])
    
    print(f"Found {len(findings)} potential secrets")
    for finding in findings:
        print(f"  {finding['file']}:{finding['line']} - {finding['type']} ({finding['severity']})")