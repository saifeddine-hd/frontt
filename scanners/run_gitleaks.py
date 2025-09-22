#!/usr/bin/env python3
"""
Gitleaks scanner wrapper for SecretHawk
"""

import subprocess
import json
import os
import tempfile
from typing import List, Dict, Any

class GitleaksScanner:
    def __init__(self, gitleaks_path: str = "gitleaks"):
        self.gitleaks_path = gitleaks_path
        self.config_file = "gitleaks.toml"
    
    def scan_directory(self, directory: str) -> List[Dict[str, Any]]:
        """Run Gitleaks scan on directory"""
        findings = []
        
        try:
            # Create temporary output file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
                temp_output = temp_file.name
            
            # Build command
            cmd = [
                self.gitleaks_path,
                "detect",
                "--source", directory,
                "--report-path", temp_output,
                "--report-format", "json",
                "--no-git"
            ]
            
            # Add config if exists
            if os.path.exists(self.config_file):
                cmd.extend(["--config", self.config_file])
            
            # Run Gitleaks
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            # Parse results
            if os.path.exists(temp_output):
                with open(temp_output, 'r') as f:
                    content = f.read().strip()
                    if content:
                        try:
                            gitleaks_results = json.loads(content)
                            findings = self._parse_results(gitleaks_results)
                        except json.JSONDecodeError:
                            print(f"Failed to parse Gitleaks output: {content}")
                
                # Cleanup
                os.unlink(temp_output)
        
        except subprocess.TimeoutExpired:
            print("Gitleaks scan timed out")
        except FileNotFoundError:
            print("Gitleaks not found. Please install from https://github.com/trufflesecurity/gitleaks")
        except Exception as e:
            print(f"Gitleaks scan failed: {e}")
        
        return findings
    
    def _parse_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse Gitleaks results into standard format"""
        findings = []
        
        for item in results:
            finding = {
                "file": item.get("File", ""),
                "line": item.get("StartLine", 0),
                "column": item.get("StartColumn", 0),
                "type": item.get("RuleID", "unknown"),
                "secret": item.get("Secret", ""),
                "severity": self._map_severity(item.get("RuleID", "")),
                "description": item.get("Description", ""),
                "author": item.get("Author", ""),
                "email": item.get("Email", ""),
                "commit": item.get("Commit", ""),
                "date": item.get("Date", ""),
                "scanner": "gitleaks"
            }
            findings.append(finding)
        
        return findings
    
    def _map_severity(self, rule_id: str) -> str:
        """Map Gitleaks rules to severity levels"""
        critical_patterns = [
            "aws-access-token", "aws-secret-key", "gcp-service-account",
            "stripe-access-token", "private-key", "rsa-private-key"
        ]
        
        high_patterns = [
            "github-pat", "gitlab-pat", "slack-bot-token",
            "discord-bot-token", "telegram-bot-token"
        ]
        
        medium_patterns = [
            "jwt", "generic-api-key", "url-secret"
        ]
        
        rule_lower = rule_id.lower()
        
        if any(pattern in rule_lower for pattern in critical_patterns):
            return "critical"
        elif any(pattern in rule_lower for pattern in high_patterns):
            return "high"
        elif any(pattern in rule_lower for pattern in medium_patterns):
            return "medium"
        else:
            return "low"

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python run_gitleaks.py <directory>")
        sys.exit(1)
    
    scanner = GitleaksScanner()
    findings = scanner.scan_directory(sys.argv[1])
    
    print(f"Found {len(findings)} secrets")
    for finding in findings:
        print(f"  {finding['file']}:{finding['line']} - {finding['type']}")