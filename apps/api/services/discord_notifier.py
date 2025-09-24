import aiohttp
import json
from typing import List, Dict, Any, Optional
from datetime import datetime

from models.finding import Finding
from models.repository import Repository
from core.config import settings

class DiscordNotifier:
    """Service to send Discord notifications for security findings"""
    
    def __init__(self):
        
        self.session = None
    
    async def get_session(self):
        if not self.session:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close_session(self):
        if self.session:
            await self.session.close()
            self.session = None
    
    async def send_security_alert(
        self, 
        webhook_url: str, 
        repository: Repository, 
        findings: List[Finding],
        scan_id: str
    ) -> bool:
        """Send security alert to Discord webhook"""
        try:
            if not findings:
                return True
            
            embed = self._create_security_embed(repository, findings, scan_id)
            payload = {
                "username": "SecretHawk Security Bot",
                "avatar_url": "https://cdn.discordapp.com/attachments/placeholder/secrethawk-logo.png",
                "embeds": [embed]
            }
            
            session = await self.get_session()
            async with session.post(webhook_url, json=payload) as response:
                if response.status == 204:
                    print(f"Discord notification sent successfully for {repository.name}")
                    return True
                else:
                    print(f"Discord notification failed: {response.status}")
                    return False
                    
        except Exception as e:
            print(f"Error sending Discord notification: {e}")
            return False
    
    async def send_scan_summary(
        self,
        webhook_url: str,
        repository: Repository,
        total_findings: int,
        critical_count: int,
        high_count: int,
        scan_id: str
    ) -> bool:
        """Send scan summary notification"""
        try:
            color = self._get_severity_color(critical_count, high_count)
            
            embed = {
                "title": f"🔍 Scan Complete: {repository.name}",
                "color": color,
                "timestamp": datetime.utcnow().isoformat(),
                "fields": [
                    {
                        "name": "📊 Summary",
                        "value": f"**Total Findings:** {total_findings}\n**Critical:** {critical_count}\n**High:** {high_count}",
                        "inline": True
                    },
                    {
                        "name": "🔗 Repository",
                        "value": f"[{repository.name}]({repository.url})",
                        "inline": True
                    },
                    {
                        "name": "📋 View Details",
                        "value": f"[Open SecretHawk Dashboard]({settings.FRONTEND_URL}/findings/{scan_id})",
                        "inline": False
                    }
                ],
                "footer": {
                    "text": "SecretHawk Security Scanner",
                    "icon_url": "https://cdn.discordapp.com/attachments/placeholder/secrethawk-icon.png"
                }
            }
            
            if total_findings == 0:
                embed["description"] = "✅ No security issues detected in this scan."
            else:
                embed["description"] = "⚠️ Security issues detected! Please review immediately."
            
            payload = {
                "username": "SecretHawk Security Bot",
                "embeds": [embed]
            }
            
            session = await self.get_session()
            async with session.post(webhook_url, json=payload) as response:
                return response.status == 204
                
        except Exception as e:
            print(f"Error sending scan summary: {e}")
            return False
    
    def _create_security_embed(
        self, 
        repository: Repository, 
        findings: List[Finding], 
        scan_id: str
    ) -> Dict[str, Any]:
        """Create Discord embed for security findings"""
        
        # Group findings by severity
        critical_findings = [f for f in findings if f.severity == "critical"]
        high_findings = [f for f in findings if f.severity == "high"]
        
        # Determine embed color based on severity
        color = 0xFF0000 if critical_findings else 0xFF8C00 if high_findings else 0xFFFF00
        
        # Create fields for findings
        fields = []
        
        # Add critical findings
        if critical_findings:
            critical_text = ""
            for finding in critical_findings[:3]:  # Limit to 3 for space
                file_name = finding.file_path.split('/')[-1]
                secret_type = finding.secret_type.replace('_', ' ').title()
                critical_text += f"🔴 **{secret_type}** in `{file_name}:{finding.line_number}`\n"
            
            if len(critical_findings) > 3:
                critical_text += f"... and {len(critical_findings) - 3} more critical issues\n"
            
            fields.append({
                "name": "🚨 Critical Issues",
                "value": critical_text,
                "inline": False
            })
        
        # Add high severity findings
        if high_findings and len(fields) < 2:  # Don't overcrowd
            high_text = ""
            for finding in high_findings[:2]:
                file_name = finding.file_path.split('/')[-1]
                secret_type = finding.secret_type.replace('_', ' ').title()
                high_text += f"🟠 **{secret_type}** in `{file_name}:{finding.line_number}`\n"
            
            if len(high_findings) > 2:
                high_text += f"... and {len(high_findings) - 2} more high issues\n"
            
            fields.append({
                "name": "⚠️ High Priority Issues",
                "value": high_text,
                "inline": False
            })
        
        # Add remediation guide
        remediation_guide = self._get_remediation_guide(findings)
        if remediation_guide:
            fields.append({
                "name": "🛠️ Immediate Actions Required",
                "value": remediation_guide,
                "inline": False
            })
        
        # Add links
        fields.append({
            "name": "🔗 Quick Links",
            "value": f"[View Repository]({repository.url})\n[SecretHawk Dashboard]({settings.FRONTEND_URL}/findings/{scan_id})",
            "inline": True
        })
        
        embed = {
            "title": f"🚨 Security Alert: {repository.name}",
            "description": f"**{len(findings)} security issues** detected in recent scan",
            "color": color,
            "fields": fields,
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {
                "text": "SecretHawk Security Scanner • Take immediate action",
                "icon_url": "https://cdn.discordapp.com/attachments/placeholder/secrethawk-icon.png"
            }
        }
        
        return embed
    
    def _get_remediation_guide(self, findings: List[Finding]) -> str:
        """Generate remediation guide based on findings"""
        guides = []
        
        # Check for different types of secrets
        secret_types = {f.secret_type for f in findings}
        
        if any('aws' in st.lower() for st in secret_types):
            guides.append("🔑 **AWS Keys:** Rotate immediately in AWS Console → IAM")
        
        if any('github' in st.lower() for st in secret_types):
            guides.append("🐙 **GitHub Tokens:** Revoke in GitHub Settings → Developer settings")
        
        if any('stripe' in st.lower() for st in secret_types):
            guides.append("💳 **Stripe Keys:** Rotate in Stripe Dashboard → API Keys")
        
        if any('private' in st.lower() or 'rsa' in st.lower() for st in secret_types):
            guides.append("🔐 **Private Keys:** Generate new keypair, update deployments")
        
        # General advice
        guides.append("📝 **Git History:** Use `git filter-branch` or BFG Repo-Cleaner")
        guides.append("🔍 **Audit:** Check all commits since key creation")
        
        return "\n".join(guides[:4])  # Limit to 4 items
    
    def _get_severity_color(self, critical_count: int, high_count: int) -> int:
        """Get Discord embed color based on severity"""
        if critical_count > 0:
            return 0xFF0000  # Red
        elif high_count > 0:
            return 0xFF8C00  # Orange
        else:
            return 0x00FF00  # Green

# Singleton instance
discord_notifier = DiscordNotifier()