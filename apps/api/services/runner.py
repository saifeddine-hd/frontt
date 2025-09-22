import os
import subprocess
import json
import re
import yaml
from typing import List
from datetime import datetime

from models.finding import Finding
from services.redact import is_in_allowlist

class ScanRunner:
    """Main scanning service that orchestrates different scanners"""
    
    def __init__(self):
        self.patterns = self._load_patterns()
        self.allowlist = self._load_allowlist()
    
    def _load_patterns(self) -> dict:
        """Load custom patterns from YAML"""
        patterns_file = "rules/patterns.yaml"
        if os.path.exists(patterns_file):
            with open(patterns_file, 'r') as f:
                return yaml.safe_load(f) or {}
        return {}
    
    def _load_allowlist(self) -> dict:
        """Load allowlist from YAML"""
        allowlist_file = "rules/allowlist.yaml"
        if os.path.exists(allowlist_file):
            with open(allowlist_file, 'r') as f:
                return yaml.safe_load(f) or {}
        return {}
    
    async def scan_directory(self, directory: str) -> List[Finding]:
        """Scan a directory for secrets"""
        findings = []
        
        # Run Gitleaks scan
        gitleaks_findings = await self._run_gitleaks(directory)
        findings.extend(gitleaks_findings)
        
        # Run regex-based scan
        regex_findings = await self._run_regex_scan(directory)
        findings.extend(regex_findings)
        
        # Filter findings through allowlist
        filtered_findings = []
        for finding in findings:
            if not is_in_allowlist(finding, self.allowlist):
                filtered_findings.append(finding)
        
        return filtered_findings
    
    async def _run_gitleaks(self, directory: str) -> List[Finding]:
        """Run Gitleaks scanner"""
        findings = []
        
        try:
            # Run gitleaks with JSON output
            cmd = [
                "gitleaks", "detect",
                "--source", directory,
                "--report-format", "json",
                "--no-git"
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.stdout:
                gitleaks_results = json.loads(result.stdout)
                
                for item in gitleaks_results:
                    finding = Finding(
                        job_id="",  # Will be set by caller
                        file_path=item.get("File", ""),
                        line_number=item.get("StartLine", 0),
                        secret_type=item.get("RuleID", "unknown"),
                        secret=item.get("Secret", ""),
                        severity=self._map_gitleaks_severity(item.get("RuleID", "")),
                        rule_id=item.get("RuleID", ""),
                        confidence=0.9,  # Gitleaks has high confidence
                        created_at=datetime.utcnow()
                    )
                    findings.append(finding)
        
        except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception) as e:
            print(f"Gitleaks scan failed: {e}")
        
        return findings
    
    async def _run_regex_scan(self, directory: str) -> List[Finding]:
        """Run custom regex-based scan"""
        findings = []
        
        # Default patterns for common secrets
        default_patterns = {
            "aws_access_key": {
                "pattern": r"AKIA[0-9A-Z]{16}",
                "severity": "critical"
            },
            "aws_secret_key": {
                "pattern": r"[A-Za-z0-9/+=]{40}",
                "severity": "critical"
            },
            "github_token": {
                "pattern": r"ghp_[A-Za-z0-9]{36}",
                "severity": "high"
            },
            "stripe_key": {
                "pattern": r"sk_live_[A-Za-z0-9]{24}",
                "severity": "critical"
            },
            "jwt_token": {
                "pattern": r"eyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*",
                "severity": "medium"
            }
        }
        
        # Merge with custom patterns
        all_patterns = {**default_patterns, **self.patterns}
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                if self._should_scan_file(file):
                    file_path = os.path.join(root, file)
                    file_findings = self._scan_file(file_path, all_patterns)
                    findings.extend(file_findings)
        
        return findings
    
    def _should_scan_file(self, filename: str) -> bool:
        """Check if file should be scanned"""
        # Skip binary files and common non-text files
        skip_extensions = {
            '.jpg', '.jpeg', '.png', '.gif', '.bmp',
            '.zip', '.tar', '.gz', '.rar',
            '.exe', '.dll', '.so', '.dylib',
            '.pdf', '.doc', '.docx'
        }
        
        _, ext = os.path.splitext(filename.lower())
        return ext not in skip_extensions
    
    def _scan_file(self, file_path: str, patterns: dict) -> List[Finding]:
        """Scan individual file with regex patterns"""
        findings = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                
                for line_no, line in enumerate(lines, 1):
                    for rule_id, rule_config in patterns.items():
                        pattern = rule_config["pattern"]
                        matches = re.finditer(pattern, line)
                        
                        for match in matches:
                            finding = Finding(
                                job_id="",  # Will be set by caller
                                file_path=file_path,
                                line_number=line_no,
                                secret_type=rule_id,
                                secret=match.group(),
                                severity=rule_config.get("severity", "medium"),
                                rule_id=rule_id,
                                confidence=rule_config.get("confidence", 0.7),
                                created_at=datetime.utcnow()
                            )
                            findings.append(finding)
        
        except Exception as e:
            print(f"Error scanning file {file_path}: {e}")
        
        return findings
    
    def _map_gitleaks_severity(self, rule_id: str) -> str:
        """Map Gitleaks rules to severity levels"""
        critical_rules = ["aws-access-token", "aws-secret-key", "stripe-access-token"]
        high_rules = ["github-pat", "gitlab-pat", "slack-bot-token"]
        
        if rule_id.lower() in critical_rules:
            return "critical"
        elif rule_id.lower() in high_rules:
            return "high"
        else:
            return "medium"