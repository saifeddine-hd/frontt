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
        self.min_confidence = 0.7  # Confidence minimale pour reporter un finding
    
    def _load_patterns(self) -> dict:
        """Load custom patterns from YAML"""
        patterns_file = "rules/patterns.yaml"
        if os.path.exists(patterns_file):
            try:
                with open(patterns_file, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                print(f"Error loading patterns file: {e}")
                return {}
        return {}
    
    def _load_allowlist(self) -> dict:
        """Load allowlist from YAML"""
        allowlist_file = "rules/allowlist.yaml"
        if os.path.exists(allowlist_file):
            try:
                with open(allowlist_file, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                print(f"Error loading allowlist file: {e}")
                return {}
        return {}
    
    def _is_file_allowlisted(self, file_path: str) -> bool:
        """Check if file should be ignored based on allowlist"""
        allowlist_files = self.allowlist.get('files', [])
        
        # Patterns par défaut pour les fichiers à ignorer
        default_file_patterns = [
            r".*/package-lock\.json$",
            r".*/yarn\.lock$", 
            r".*/composer\.lock$",
            r".*/Pipfile\.lock$",
            r".*/poetry\.lock$",
            r".*/node_modules/.*",
            r".*/vendor/.*",
            r".*/build/.*",
            r".*/dist/.*",
            r".*/target/.*",
            r".*\.zip$",
            r".*\.tar\.gz$",
            r".*\.jar$",
            r".*\.war$",
            r".*\.min\.js$",
            r".*\.min\.css$"
        ]
        
        # Combiner patterns par défaut et personnalisés
        all_patterns = default_file_patterns + allowlist_files
        
        # Normaliser le chemin pour la comparaison
        normalized_path = file_path.replace('\\', '/')
        
        for pattern in all_patterns:
            try:
                if re.match(pattern, normalized_path):
                    return True
            except re.error as e:
                print(f"Invalid allowlist file pattern '{pattern}': {e}")
                continue
        
        return False
    
    async def scan_directory(self, directory: str) -> List[Finding]:
        """Scan a directory for secrets"""
        findings = []
        
        print(f"Starting scan of directory: {directory}")
        
        # Run Gitleaks scan
        try:
            gitleaks_findings = await self._run_gitleaks(directory)
            findings.extend(gitleaks_findings)
            print(f"Gitleaks found {len(gitleaks_findings)} findings")
        except Exception as e:
            print(f"Gitleaks scan failed: {e}")
        
        # Run regex-based scan
        try:
            regex_findings = await self._run_regex_scan(directory)
            findings.extend(regex_findings)
            print(f"Regex scan found {len(regex_findings)} findings")
        except Exception as e:
            print(f"Regex scan failed: {e}")
        
        # Filter findings through allowlist and confidence
        filtered_findings = []
        for finding in findings:
            try:
                # Vérifier allowlist
                if is_in_allowlist(finding, self.allowlist):
                    print(f"Finding filtered by allowlist: {finding.file_path}:{finding.line_number}")
                    continue
                
                # Vérifier confidence minimale
                if finding.confidence < self.min_confidence:
                    print(f"Finding filtered by low confidence ({finding.confidence}): {finding.file_path}:{finding.line_number}")
                    continue
                
                filtered_findings.append(finding)
                
            except Exception as e:
                print(f"Error filtering finding: {e}")
                # Include finding if filtering fails
                filtered_findings.append(finding)
        
        print(f"Total findings after filtering: {len(filtered_findings)} (removed {len(findings) - len(filtered_findings)} low-confidence/allowlisted findings)")
        return filtered_findings
    
    async def _run_gitleaks(self, directory: str) -> List[Finding]:
        """Run Gitleaks scanner"""
        findings = []
        
        try:
            # Check if gitleaks is available
            result = subprocess.run(
                ["gitleaks", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                print("Gitleaks not available, skipping gitleaks scan")
                return findings
            
            # Run gitleaks with JSON output
            cmd = [
                "gitleaks", "detect",
                "--source", directory,
                "--report-format", "json",
                "--no-git",
                "--verbose"
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            # Gitleaks returns exit code 1 when secrets are found, which is normal
            if result.stdout:
                try:
                    gitleaks_results = json.loads(result.stdout)
                    
                    for item in gitleaks_results:
                        file_path = item.get("File", "")
                        
                        # Skip allowlisted files
                        if self._is_file_allowlisted(file_path):
                            print(f"Skipping allowlisted file from Gitleaks: {file_path}")
                            continue
                        
                        finding = Finding(
                            job_id="",  # Will be set by caller
                            file_path=file_path,
                            line_number=item.get("StartLine", 0),
                            secret_type=item.get("RuleID", "unknown"),
                            secret=item.get("Secret", ""),
                            severity=self._map_gitleaks_severity(item.get("RuleID", "")),
                            rule_id=item.get("RuleID", ""),
                            confidence=0.9,  # Gitleaks has high confidence
                            created_at=datetime.utcnow()
                        )
                        findings.append(finding)
                except json.JSONDecodeError as e:
                    print(f"Error parsing gitleaks JSON output: {e}")
        
        except subprocess.TimeoutExpired:
            print("Gitleaks scan timed out")
        except FileNotFoundError:
            print("Gitleaks not found, skipping gitleaks scan")
        except Exception as e:
            print(f"Gitleaks scan failed: {e}")
        
        return findings
    
    async def _run_regex_scan(self, directory: str) -> List[Finding]:
        """Run custom regex-based scan"""
        findings = []
        
        # Default patterns for common secrets (avec confidence ajustée)
        default_patterns = {
            "aws_access_key": {
                "pattern": r"\bAKIA[0-9A-Z]{16}\b",
                "severity": "critical",
                "confidence": 0.95  # Très confiant pour AKIA pattern
            },
            "aws_secret_key": {
                "pattern": r"\b[A-Za-z0-9/+=]{40}\b",
                "severity": "critical",
                "confidence": 0.6  # Plus faible car pattern générique
            },
            "github_token": {
                "pattern": r"\bghp_[A-Za-z0-9]{36}\b",
                "severity": "high",
                "confidence": 0.95
            },
            "github_fine_grained_pat": {
                "pattern": r"\bgithub_pat_[A-Za-z0-9_]{82}\b",
                "severity": "high",
                "confidence": 0.95
            },
            "stripe_secret_key": {
                "pattern": r"\bsk_live_[A-Za-z0-9]{24}\b",
                "severity": "critical",
                "confidence": 0.95
            },
            "stripe_publishable_key": {
                "pattern": r"\bpk_live_[A-Za-z0-9]{24}\b",
                "severity": "medium",
                "confidence": 0.9
            },
            "jwt_token": {
                "pattern": r"\beyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*\b",
                "severity": "medium",
                "confidence": 0.7
            },
            "slack_token": {
                "pattern": r"\bxox[baprs]-[A-Za-z0-9-]{8,}\b",
                "severity": "high",
                "confidence": 0.9
            },
            "google_api_key": {
                "pattern": r"\bAIza[0-9A-Za-z_-]{35}\b",
                "severity": "high",
                "confidence": 0.9
            },
            "private_key_header": {
                "pattern": r"-----BEGIN[A-Z ]+PRIVATE KEY-----",
                "severity": "critical",
                "confidence": 0.95
            },
            "database_url": {
                "pattern": r"\b(postgresql|mysql|mongodb)://[^\s'\"]+\b",
                "severity": "critical",
                "confidence": 0.85
            },
            "generic_api_key": {
                "pattern": r"\b[aA]pi[_-]?[kK]ey['\"]?\s*[:=]\s*['\"]?[A-Za-z0-9_-]{16,}['\"]?",
                "severity": "medium",
                "confidence": 0.5  # Faible car très générique
            },
            "generic_secret": {
                "pattern": r"\b[sS]ecret['\"]?\s*[:=]\s*['\"]?[A-Za-z0-9_-]{16,}['\"]?",
                "severity": "medium",
                "confidence": 0.5
            },
            "generic_token": {
                "pattern": r"\b[tT]oken['\"]?\s*[:=]\s*['\"]?[A-Za-z0-9_-]{16,}['\"]?",
                "severity": "medium",
                "confidence": 0.5
            }
        }
        
        # Merge with custom patterns
        all_patterns = {**default_patterns, **self.patterns}
        
        scanned_files = 0
        skipped_files = 0
        
        for root, dirs, files in os.walk(directory):
            # Skip certain directories
            dirs[:] = [d for d in dirs if not self._should_skip_directory(d)]
            
            for file in files:
                if not self._should_scan_file(file):
                    continue
                    
                file_path = os.path.join(root, file)
                
                # Check if file is allowlisted
                if self._is_file_allowlisted(file_path):
                    skipped_files += 1
                    if skipped_files % 10 == 0:
                        print(f"Skipped {skipped_files} allowlisted files")
                    continue
                
                try:
                    file_findings = self._scan_file(file_path, all_patterns)
                    findings.extend(file_findings)
                    scanned_files += 1
                    
                    if scanned_files % 100 == 0:
                        print(f"Scanned {scanned_files} files, found {len(findings)} potential secrets so far")
                
                except Exception as e:
                    print(f"Error scanning file {file_path}: {e}")
                    continue
        
        print(f"Regex scan completed. Scanned {scanned_files} files, skipped {skipped_files} allowlisted files.")
        return findings
    
    def _should_skip_directory(self, dirname: str) -> bool:
        """Check if directory should be skipped"""
        skip_dirs = {
            'node_modules', '__pycache__', '.git', '.vscode', '.idea',
            'venv', 'env', '.env', 'build', 'dist', 'target',
            '.pytest_cache', '.mypy_cache', '.coverage', '.tox',
            'vendor', 'third_party', 'external', '.venv',
            '.sass-cache', 'bower_components', '.nuxt', '.next'
        }
        return dirname in skip_dirs or dirname.startswith('.')
    
    def _should_scan_file(self, filename: str) -> bool:
        """Check if file should be scanned"""
        # Skip binary files and common non-text files
        skip_extensions = {
            # Images
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.ico', '.webp',
            # Archives
            '.zip', '.tar', '.gz', '.rar', '.7z', '.bz2', '.xz',
            # Executables and libraries
            '.exe', '.dll', '.so', '.dylib', '.a', '.lib',
            # Office documents
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
            # Media files
            '.mp3', '.mp4', '.avi', '.mov', '.wav', '.flac', '.ogg',
            # Compiled files
            '.pyc', '.pyo', '.class', '.o', '.obj',
            # Fonts
            '.woff', '.woff2', '.ttf', '.eot', '.otf',
            # Other binary
            '.bin', '.dat', '.db', '.sqlite', '.sqlite3'
        }
        
        _, ext = os.path.splitext(filename.lower())
        if ext in skip_extensions:
            return False
        
        # Skip very large files (> 10MB) to avoid memory issues
        try:
            file_path = filename if os.path.isabs(filename) else os.path.join(os.getcwd(), filename)
            if os.path.getsize(file_path) > 10 * 1024 * 1024:
                return False
        except (OSError, FileNotFoundError):
            # If we can't get file size, assume it's scannable
            pass
        
        return True
    
    def _scan_file(self, file_path: str, patterns: dict) -> List[Finding]:
        """Scan individual file with regex patterns"""
        findings = []
        
        try:
            # Try to read the file with UTF-8 encoding first
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                # If UTF-8 fails, try with latin-1 (which accepts all byte values)
                try:
                    with open(file_path, 'r', encoding='latin-1') as f:
                        content = f.read()
                except Exception:
                    # If all encoding attempts fail, skip this file
                    return findings
            
            # Split content into lines for line number tracking
            lines = content.split('\n')
            
            for line_no, line in enumerate(lines, 1):
                for rule_id, rule_config in patterns.items():
                    try:
                        # Get pattern string and other config
                        if isinstance(rule_config, dict):
                            pattern_str = rule_config.get("pattern", "")
                            severity = rule_config.get("severity", "medium")
                            base_confidence = rule_config.get("confidence", 0.7)
                        else:
                            # Handle case where rule_config is just a string pattern
                            pattern_str = str(rule_config)
                            severity = "medium"
                            base_confidence = 0.7
                        
                        if not pattern_str:
                            continue
                        
                        # Compile and use regex pattern
                        try:
                            compiled_pattern = re.compile(pattern_str, re.IGNORECASE)
                            matches = compiled_pattern.finditer(line)
                            
                            for match in matches:
                                matched_text = match.group().strip()
                                
                                # Skip empty matches or very short ones
                                if len(matched_text) < 3:
                                    continue
                                
                                # Calculer confidence ajustée selon le contexte
                                adjusted_confidence = self._calculate_adjusted_confidence(
                                    matched_text, rule_id, file_path, line, base_confidence
                                )
                                
                                # Skip si confidence trop faible
                                if adjusted_confidence < 0.3:
                                    continue
                                
                                # Create relative path for cleaner display
                                try:
                                    rel_path = os.path.relpath(file_path)
                                except ValueError:
                                    rel_path = file_path
                                
                                finding = Finding(
                                    job_id="",  # Will be set by caller
                                    file_path=rel_path,
                                    line_number=line_no,
                                    secret_type=rule_id,
                                    secret=matched_text,
                                    severity=severity,
                                    rule_id=rule_id,
                                    confidence=adjusted_confidence,
                                    created_at=datetime.utcnow()
                                )
                                findings.append(finding)
                        
                        except re.error as e:
                            print(f"Invalid regex pattern for rule '{rule_id}': {e}")
                            continue
                    
                    except Exception as e:
                        print(f"Error applying pattern '{rule_id}' to {file_path} line {line_no}: {e}")
                        continue
        
        except Exception as e:
            print(f"Error scanning file {file_path}: {e}")
        
        return findings
    
    def _calculate_adjusted_confidence(self, match: str, rule_id: str, file_path: str, line_context: str, base_confidence: float) -> float:
        """Calculate adjusted confidence based on context and false positive detection"""
        confidence = base_confidence
        match_lower = match.lower().strip()
        
        # Réduire confidence pour placeholders évidents
        false_positive_keywords = {
            'example', 'test', 'demo', 'placeholder', 'fake', 'dummy', 'sample',
            'your_key_here', 'insert_key_here', 'put_key_here', 'replace_with',
            'todo', 'fixme', 'xxx', 'yyy', 'zzz', 'abc', '123',
            'lorem', 'ipsum', 'dolor'
        }
        
        for keyword in false_positive_keywords:
            if keyword in match_lower:
                confidence *= 0.1  # Très faible confidence
                
        # Patterns évidemment faux
        false_positive_patterns = [
            r'^x+$',        # All x's
            r'^\*+$',       # All asterisks  
            r'^0+$',        # All zeros
            r'^1+$',        # All ones
            r'^[a-z]+$',    # All lowercase letters
            r'^[A-Z]+$',    # All uppercase letters
            r'^\d+$',       # All digits
            r'^\$\{.*\}$',  # Environment variable placeholder
            r'^<.*>$',      # XML/HTML placeholder
            r'^\[.*\]$',    # Bracket placeholder
        ]
        
        for pattern in false_positive_patterns:
            if re.match(pattern, match_lower):
                confidence *= 0.1
        
        # Contexte du fichier
        file_ext = os.path.splitext(file_path.lower())[1]
        filename = os.path.basename(file_path.lower())
        
        # Réduire confidence dans certains types de fichiers
        if file_ext in ['.md', '.txt', '.rst']:
            confidence *= 0.5  # Documentation souvent des exemples
        elif filename in ['readme.md', 'changelog.md', 'contributing.md']:
            confidence *= 0.3
        elif 'test' in filename or 'spec' in filename:
            confidence *= 0.4  # Fichiers de test souvent des fakes
        elif filename.endswith('.lock'):
            confidence *= 0.1  # Fichiers lock très suspects
        
        # Contexte de ligne
        line_lower = line_context.lower()
        if any(word in line_lower for word in ['example', 'demo', 'test', 'placeholder']):
            confidence *= 0.3
        elif 'const' in line_lower or 'var' in line_lower or 'let' in line_lower:
            confidence *= 1.1  # Code réel plus probable
        elif line_lower.strip().startswith('#'):
            confidence *= 0.5  # Commentaires moins probables
        
        # Rule-specific adjustments
        if rule_id == "aws_secret_key":
            # Pattern très générique, besoin de plus de validation
            if not self._looks_like_base64(match):
                confidence *= 0.3
            if len(match) != 40:
                confidence *= 0.5
                
        elif rule_id == "jwt_token":
            parts = match.split('.')
            if len(parts) != 3:
                confidence *= 0.2
            elif len(match) < 50:
                confidence *= 0.4
                
        elif rule_id in ["generic_api_key", "generic_secret", "generic_token"]:
            # Patterns très génériques, être très strict
            if len(match) < 16:
                confidence *= 0.3
            if not re.search(r'[A-Za-z]', match) or not re.search(r'[0-9]', match):
                confidence *= 0.2
        
        return max(0.0, min(1.0, confidence))
    
    def _looks_like_base64(self, text: str) -> bool:
        """Check if text looks like base64"""
        if not text:
            return False
        
        # Base64 uses A-Z, a-z, 0-9, +, /
        valid_chars = re.match(r'^[A-Za-z0-9+/]*={0,2}$', text)
        if not valid_chars:
            return False
        
        # Should have good mix of character types
        has_upper = bool(re.search(r'[A-Z]', text))
        has_lower = bool(re.search(r'[a-z]', text))
        has_digits = bool(re.search(r'[0-9]', text))
        
        return sum([has_upper, has_lower, has_digits]) >= 2
    
    def _map_gitleaks_severity(self, rule_id: str) -> str:
        """Map Gitleaks rules to severity levels"""
        rule_id_lower = rule_id.lower()
        
        critical_rules = {
            "aws-access-token", "aws-secret-key", "stripe-access-token",
            "private-key", "rsa-private-key", "ssh-private-key",
            "gcp-service-account", "azure-storage-account-key"
        }
        
        high_rules = {
            "github-pat", "gitlab-pat", "slack-bot-token", "slack-webhook",
            "google-api-key", "sendgrid-api-token", "twilio-api-key",
            "mailgun-api-key", "square-access-token"
        }
        
        medium_rules = {
            "jwt", "bearer-token", "basic-auth", "api-key-generic"
        }
        
        if any(rule in rule_id_lower for rule in critical_rules):
            return "critical"
        elif any(rule in rule_id_lower for rule in high_rules):
            return "high"
        elif any(rule in rule_id_lower for rule in medium_rules):
            return "medium"
        else:
            return "low"