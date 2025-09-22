#!/usr/bin/env python3
"""
SecretHawk CLI - Local secret scanner
"""

import os
import sys
import json
import argparse
import subprocess
import yaml
from typing import List, Dict, Any
from pathlib import Path
import re
import tempfile

class SecretHawkCLI:
    def __init__(self):
        self.ignore_patterns = self._load_ignore_patterns()
        self.patterns = self._load_patterns()
        self.allowlist = self._load_allowlist()
    
    def _load_ignore_patterns(self) -> List[str]:
        """Load ignore patterns from .secrethawkignore"""
        ignore_file = ".secrethawkignore"
        patterns = []
        
        # Default ignore patterns
        default_patterns = [
            ".git/",
            "node_modules/",
            "vendor/",
            "*.log",
            "*.tmp",
            "*.cache",
            "__pycache__/",
            "*.pyc",
            ".DS_Store",
            "*.zip",
            "*.tar.gz"
        ]
        patterns.extend(default_patterns)
        
        if os.path.exists(ignore_file):
            with open(ignore_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        patterns.append(line)
        
        return patterns
    
    def _load_patterns(self) -> Dict[str, Any]:
        """Load scanning patterns"""
        # Default patterns
        patterns = {
            "aws_access_key": {
                "pattern": r"AKIA[0-9A-Z]{16}",
                "severity": "critical",
                "description": "AWS Access Key ID"
            },
            "aws_secret_key": {
                "pattern": r"[A-Za-z0-9/+=]{40}",
                "severity": "critical",
                "description": "AWS Secret Access Key"
            },
            "github_token": {
                "pattern": r"ghp_[A-Za-z0-9]{36}",
                "severity": "high",
                "description": "GitHub Personal Access Token"
            },
            "github_oauth": {
                "pattern": r"gho_[A-Za-z0-9]{36}",
                "severity": "high",
                "description": "GitHub OAuth Token"
            },
            "stripe_key": {
                "pattern": r"sk_live_[A-Za-z0-9]{24}",
                "severity": "critical",
                "description": "Stripe Live Secret Key"
            },
            "stripe_publishable": {
                "pattern": r"pk_live_[A-Za-z0-9]{24}",
                "severity": "medium",
                "description": "Stripe Live Publishable Key"
            },
            "slack_token": {
                "pattern": r"xox[baprs]-[A-Za-z0-9-]{10,}",
                "severity": "high",
                "description": "Slack Token"
            },
            "jwt_token": {
                "pattern": r"eyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*",
                "severity": "medium",
                "description": "JSON Web Token"
            },
            "private_key": {
                "pattern": r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
                "severity": "critical",
                "description": "Private Key"
            },
            "google_api_key": {
                "pattern": r"AIza[0-9A-Za-z_-]{35}",
                "severity": "high",
                "description": "Google API Key"
            }
        }
        
        # Try to load custom patterns
        patterns_file = "patterns.yaml"
        if os.path.exists(patterns_file):
            with open(patterns_file, 'r') as f:
                custom = yaml.safe_load(f)
                if custom and 'custom_patterns' in custom:
                    patterns.update(custom['custom_patterns'])
        
        return patterns
    
    def _load_allowlist(self) -> Dict[str, Any]:
        """Load allowlist configuration"""
        allowlist_file = "allowlist.yaml"
        if os.path.exists(allowlist_file):
            with open(allowlist_file, 'r') as f:
                return yaml.safe_load(f) or {}
        return {}
    
    def _should_ignore_file(self, file_path: str) -> bool:
        """Check if file should be ignored"""
        for pattern in self.ignore_patterns:
            if pattern.endswith('/'):
                # Directory pattern
                if pattern[:-1] in file_path:
                    return True
            elif '*' in pattern:
                # Glob pattern (basic implementation)
                regex_pattern = pattern.replace('*', '.*')
                if re.search(regex_pattern, os.path.basename(file_path)):
                    return True
            else:
                # Exact match
                if pattern in file_path:
                    return True
        return False
    
    def _is_in_allowlist(self, finding: Dict[str, Any]) -> bool:
        """Check if finding should be ignored"""
        if not self.allowlist:
            return False
        
        # Check file patterns
        file_patterns = self.allowlist.get("files", [])
        for pattern in file_patterns:
            if re.search(pattern, finding["file"]):
                return True
        
        # Check secret patterns
        secret_patterns = self.allowlist.get("secrets", [])
        for pattern in secret_patterns:
            if re.search(pattern, finding["secret"]):
                return True
        
        return False
    
    def _redact_secret(self, secret: str) -> str:
        """Redact secret for safe display"""
        if len(secret) <= 8:
            return "*" * len(secret)
        return f"{secret[:4]}{'*' * (len(secret) - 8)}{secret[-4:]}"
    
    def _scan_file_with_regex(self, file_path: str) -> List[Dict[str, Any]]:
        """Scan file with regex patterns"""
        findings = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                
                for line_no, line in enumerate(lines, 1):
                    for rule_id, rule_config in self.patterns.items():
                        pattern = rule_config["pattern"]
                        matches = re.finditer(pattern, line)
                        
                        for match in matches:
                            finding = {
                                "file": file_path,
                                "line": line_no,
                                "type": rule_id,
                                "secret": match.group(),
                                "secret_redacted": self._redact_secret(match.group()),
                                "severity": rule_config.get("severity", "medium"),
                                "description": rule_config.get("description", ""),
                                "scanner": "regex"
                            }
                            
                            if not self._is_in_allowlist(finding):
                                findings.append(finding)
        
        except Exception as e:
            print(f"Error scanning {file_path}: {e}")
        
        return findings
    
    def _run_gitleaks(self, directory: str) -> List[Dict[str, Any]]:
        """Run Gitleaks scanner"""
        findings = []
        
        try:
            # Create temporary output file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
                temp_output = temp_file.name
            
            # Run gitleaks
            cmd = [
                "gitleaks", "detect",
                "--source", directory,
                "--report-path", temp_output,
                "--report-format", "json",
                "--no-git"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Read results
            if os.path.exists(temp_output):
                try:
                    with open(temp_output, 'r') as f:
                        content = f.read().strip()
                        if content:
                            gitleaks_results = json.loads(content)
                            
                            for item in gitleaks_results:
                                finding = {
                                    "file": item.get("File", ""),
                                    "line": item.get("StartLine", 0),
                                    "type": item.get("RuleID", "unknown"),
                                    "secret": item.get("Secret", ""),
                                    "secret_redacted": self._redact_secret(item.get("Secret", "")),
                                    "severity": self._map_gitleaks_severity(item.get("RuleID", "")),
                                    "description": item.get("Description", ""),
                                    "scanner": "gitleaks"
                                }
                                findings.append(finding)
                except json.JSONDecodeError:
                    pass
                
                # Cleanup
                os.unlink(temp_output)
        
        except FileNotFoundError:
            print("Warning: Gitleaks not found. Install from https://github.com/trufflesecurity/gitleaks")
        except Exception as e:
            print(f"Gitleaks scan failed: {e}")
        
        return findings
    
    def _map_gitleaks_severity(self, rule_id: str) -> str:
        """Map Gitleaks rules to severity levels"""
        critical_rules = ["aws-access-token", "aws-secret-key", "stripe-access-token"]
        high_rules = ["github-pat", "gitlab-pat", "slack-bot-token"]
        
        if any(critical in rule_id.lower() for critical in critical_rules):
            return "critical"
        elif any(high in rule_id.lower() for high in high_rules):
            return "high"
        else:
            return "medium"
    
    def scan_directory(self, directory: str) -> List[Dict[str, Any]]:
        """Scan directory for secrets"""
        print(f"🔍 Scanning directory: {directory}")
        
        all_findings = []
        files_scanned = 0
        
        # Run Gitleaks if available
        print("📊 Running Gitleaks scanner...")
        gitleaks_findings = self._run_gitleaks(directory)
        all_findings.extend(gitleaks_findings)
        
        # Run regex scan
        print("🔎 Running regex scanner...")
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                
                if self._should_ignore_file(file_path):
                    continue
                
                if self._should_scan_file(file):
                    findings = self._scan_file_with_regex(file_path)
                    all_findings.extend(findings)
                    files_scanned += 1
        
        print(f"✅ Scanned {files_scanned} files")
        print(f"🚨 Found {len(all_findings)} potential secrets")
        
        return all_findings
    
    def _should_scan_file(self, filename: str) -> bool:
        """Check if file should be scanned"""
        # Extensions à ignorer
        skip_extensions = {
            '.jpg', '.jpeg', '.png', '.gif', '.bmp',
            '.zip', '.tar', '.gz', '.rar',
            '.exe', '.dll', '.so', '.dylib',
            '.pdf', '.doc', '.docx', '.xls', '.xlsx',
            '.mp3', '.mp4', '.avi', '.mov',
            '.log', '.tmp', '.temp', '.cache',
            '.pyc', '.pyo', '.class'
        }

        # Fichiers de lock et configuration d'exemple
        skip_files = {
            'package-lock.json',
            'yarn.lock',
            'pnpm-lock.yaml',
            '.env.example',
            'config.example.json',
            'secrets.example.yaml'
        }

        _, ext = os.path.splitext(filename.lower())
        base = os.path.basename(filename.lower())

        return ext not in skip_extensions and base not in skip_files

    
    def display_findings(self, findings: List[Dict[str, Any]]):
        """Display findings in a readable format"""
        if not findings:
            print("✅ No secrets found!")
            return
        
        # Group by severity
        by_severity = {}
        for finding in findings:
            severity = finding["severity"]
            if severity not in by_severity:
                by_severity[severity] = []
            by_severity[severity].append(finding)
        
        # Display summary
        print("\n📊 Summary:")
        for severity in ["critical", "high", "medium", "low"]:
            count = len(by_severity.get(severity, []))
            if count > 0:
                emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🔵"}
                print(f"  {emoji.get(severity, '⚪')} {severity.title()}: {count}")
        
        # Display detailed findings
        print("\n🔍 Detailed Findings:")
        for severity in ["critical", "high", "medium", "low"]:
            severity_findings = by_severity.get(severity, [])
            if severity_findings:
                print(f"\n{severity.upper()} FINDINGS:")
                for finding in severity_findings:
                    print(f"  📄 File: {finding['file']}:{finding['line']}")
                    print(f"  🏷️  Type: {finding['type']}")
                    print(f"  🔒 Secret: {finding['secret_redacted']}")
                    print(f"  📝 Description: {finding.get('description', 'N/A')}")
                    print(f"  🔧 Scanner: {finding['scanner']}")
                    print()
    
    def export_findings(self, findings: List[Dict[str, Any]], output_file: str):
        """Export findings to JSON file"""
        output_data = {
            "scan_timestamp": str(os.path.getctime('.')),
            "total_findings": len(findings),
            "summary": {},
            "findings": findings
        }
        
        # Create summary
        for finding in findings:
            severity = finding["severity"]
            output_data["summary"][severity] = output_data["summary"].get(severity, 0) + 1
        
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        print(f"📁 Results exported to: {output_file}")

def main():
    parser = argparse.ArgumentParser(description="SecretHawk CLI - Local secret scanner")
    parser.add_argument("command", choices=["scan"], help="Command to run")
    parser.add_argument("directory", help="Directory to scan")
    parser.add_argument("--output", "-o", help="Output JSON file")
    parser.add_argument("--patterns", help="Custom patterns YAML file")
    
    args = parser.parse_args()
    
    scanner = SecretHawkCLI()
    
    if args.command == "scan":
        if not os.path.exists(args.directory):
            print(f"Error: Directory '{args.directory}' does not exist")
            sys.exit(1)
        
        findings = scanner.scan_directory(args.directory)
        scanner.display_findings(findings)
        
        if args.output:
            scanner.export_findings(findings, args.output)

if __name__ == "__main__":
    main()