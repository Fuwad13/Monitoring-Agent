import aiosmtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Optional
from datetime import datetime
from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailNotificationService:
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.username = settings.SMTP_USERNAME
        self.password = settings.SMTP_PASSWORD
        self.from_email = settings.EMAIL_FROM
        self.from_name = settings.EMAIL_FROM_NAME
        logger.info(f"📧 Email service initialized - Host: {self.smtp_host}:{self.smtp_port}")

    async def send_change_notification(
        self, 
        to_email: str, 
        target_url: str, 
        ai_analysis: Dict,
        target_type: str,
        user_name: str = "User"
    ) -> bool:
        """Send AI-powered change notification email"""
        try:
            subject = self._generate_subject(ai_analysis, target_type)
            html_content = self._generate_html_content(
                target_url=target_url,
                ai_analysis=ai_analysis,
                target_type=target_type,
                user_name=user_name
            )
            
            return await self._send_email(
                to_email=to_email,
                subject=subject,
                html_content=html_content
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to send change notification: {e}")
            return False

    async def send_insights_notification(
        self,
        to_email: str,
        target_url: str,
        ai_insights: Dict,
        target_type: str,
        user_name: str = "User"
    ) -> bool:
        """Send initial profile insights email"""
        try:
            subject = f"📊 Profile Insights - {self._get_target_name(target_url)}"
            html_content = self._generate_insights_html(
                target_url=target_url,
                ai_insights=ai_insights,
                target_type=target_type,
                user_name=user_name
            )
            
            return await self._send_email(
                to_email=to_email,
                subject=subject,
                html_content=html_content
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to send insights notification: {e}")
            return False

    async def send_summary_email(
        self,
        to_email: str,
        changes_summary: List[Dict],
        user_name: str = "User"
    ) -> bool:
        """Send daily/weekly summary email"""
        try:
            subject = f"📈 Monitoring Summary - {len(changes_summary)} Updates"
            html_content = self._generate_summary_html(
                changes_summary=changes_summary,
                user_name=user_name
            )
            
            return await self._send_email(
                to_email=to_email,
                subject=subject,
                html_content=html_content
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to send summary email: {e}")
            return False

    def _generate_subject(self, ai_analysis: Dict, target_type: str) -> str:
        """Generate email subject based on AI analysis"""
        priority = ai_analysis.get("alert_priority", "medium").upper()
        importance = ai_analysis.get("importance_score", 5)
        
        priority_emoji = {
            "HIGH": "🔥",
            "MEDIUM": "⚡",
            "LOW": "📊"
        }
        
        emoji = priority_emoji.get(priority, "📊")
        
        if target_type == "linkedin_profile":
            return f"{emoji} LinkedIn Profile Update - {priority} Priority (Score: {importance}/10)"
        elif target_type == "linkedin_company":
            return f"{emoji} Company Page Update - {priority} Priority (Score: {importance}/10)"
        else:
            return f"{emoji} Website Update - {priority} Priority"

    def _generate_html_content(
        self, 
        target_url: str, 
        ai_analysis: Dict, 
        target_type: str,
        user_name: str
    ) -> str:
        """Generate rich HTML email content"""
        
        priority = ai_analysis.get("alert_priority", "medium")
        importance = ai_analysis.get("importance_score", 5)
        summary = ai_analysis.get("change_summary", "Changes detected")
        key_changes = ai_analysis.get("key_changes", [])
        insights = ai_analysis.get("insights", {})
        suggested_action = ai_analysis.get("suggested_action", "Monitor for further changes")
        
        # Priority styling
        priority_colors = {
            "high": "#FF4444",
            "medium": "#FF8800", 
            "low": "#4CAF50"
        }
        
        priority_color = priority_colors.get(priority.lower(), "#4CAF50")
        target_name = self._get_target_name(target_url)
        
        # Build changes list
        changes_html = ""
        if key_changes:
            changes_html = "<ul style='margin: 10px 0; padding-left: 20px;'>"
            for change in key_changes[:5]:  # Top 5 changes
                category = change.get("category", "").title()
                description = change.get("description", "")
                if category and description:
                    changes_html += f"<li style='margin: 5px 0;'><strong>{category}:</strong> {description}</li>"
            changes_html += "</ul>"
        
        # Build insights section
        insights_html = ""
        if insights:
            insights_html = "<div style='background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 15px 0;'>"
            insights_html += "<h3 style='margin: 0 0 10px 0; color: #333;'>🔍 AI Insights</h3>"
            
            if insights.get("career_movement"):
                insights_html += f"<p><strong>Career Movement:</strong> {insights['career_movement']}</p>"
            if insights.get("skill_development"):
                insights_html += f"<p><strong>Skill Development:</strong> {insights['skill_development']}</p>"
            if insights.get("engagement_potential"):
                insights_html += f"<p><strong>Engagement Potential:</strong> {insights['engagement_potential']}</p>"
            if insights.get("notable_updates"):
                insights_html += f"<p><strong>Notable Updates:</strong> {insights['notable_updates']}</p>"
                
            insights_html += "</div>"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>Monitoring Alert</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            
            <!-- Header -->
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px 10px 0 0; text-align: center;">
                <h1 style="margin: 0; font-size: 24px;">🤖 AI Monitoring Alert</h1>
                <p style="margin: 5px 0 0 0; opacity: 0.9;">Powered by Gemini AI</p>
            </div>
            
            <!-- Content -->
            <div style="background: white; border: 1px solid #e0e0e0; border-top: none; padding: 25px; border-radius: 0 0 10px 10px;">
                
                <!-- Greeting -->
                <p style="margin: 0 0 20px 0; font-size: 16px;">Hello {user_name},</p>
                
                <!-- Priority Badge -->
                <div style="background: {priority_color}; color: white; padding: 8px 15px; border-radius: 20px; display: inline-block; font-weight: bold; margin-bottom: 20px;">
                    {priority.upper()} PRIORITY • Score: {importance}/10
                </div>
                
                <!-- Target Info -->
                <div style="background: #f5f5f5; padding: 15px; border-radius: 8px; margin: 15px 0;">
                    <h3 style="margin: 0 0 10px 0; color: #333;">🎯 Target Information</h3>
                    <p style="margin: 5px 0;"><strong>Name:</strong> {target_name}</p>
                    <p style="margin: 5px 0;"><strong>Type:</strong> {target_type.replace('_', ' ').title()}</p>
                    <p style="margin: 5px 0;"><strong>URL:</strong> <a href="{target_url}" style="color: #667eea;">{target_url}</a></p>
                    <p style="margin: 5px 0;"><strong>Detected:</strong> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
                </div>
                
                <!-- Summary -->
                <div style="margin: 20px 0;">
                    <h3 style="color: #333; margin: 0 0 10px 0;">📋 Change Summary</h3>
                    <p style="background: #e8f4fd; padding: 15px; border-left: 4px solid #2196F3; border-radius: 4px; margin: 10px 0;">
                        {summary}
                    </p>
                </div>
                
                <!-- Key Changes -->
                {f'''
                <div style="margin: 20px 0;">
                    <h3 style="color: #333; margin: 0 0 10px 0;">🔍 Key Changes Detected</h3>
                    {changes_html}
                </div>
                ''' if changes_html else ''}
                
                <!-- AI Insights -->
                {insights_html}
                
                <!-- Suggested Action -->
                <div style="background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="margin: 0 0 10px 0; color: #856404;">💡 Suggested Action</h3>
                    <p style="margin: 0; color: #856404;">{suggested_action}</p>
                </div>
                
                <!-- Footer -->
                <div style="border-top: 1px solid #e0e0e0; padding-top: 20px; margin-top: 30px; text-align: center; color: #666;">
                    <p style="margin: 0; font-size: 14px;">
                        This alert was generated by your AI-powered Monitoring Agent<br>
                        <small>Powered by Google Gemini AI • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</small>
                    </p>
                </div>
                
            </div>
        </body>
        </html>
        """
        
        return html_content

    def _generate_insights_html(
        self,
        target_url: str,
        ai_insights: Dict,
        target_type: str,
        user_name: str
    ) -> str:
        """Generate HTML for initial profile insights"""
        target_name = self._get_target_name(target_url)
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>Profile Insights</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            
            <!-- Header -->
            <div style="background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%); color: white; padding: 20px; border-radius: 10px 10px 0 0; text-align: center;">
                <h1 style="margin: 0; font-size: 24px;">💡 Profile Insights</h1>
                <p style="margin: 5px 0 0 0; opacity: 0.9;">AI-Powered Analysis</p>
            </div>
            
            <!-- Content -->
            <div style="background: white; border: 1px solid #e0e0e0; border-top: none; padding: 25px; border-radius: 0 0 10px 10px;">
                
                <p style="margin: 0 0 20px 0; font-size: 16px;">Hello {user_name},</p>
                
                <p>Your monitoring agent has analyzed the profile and extracted key insights:</p>
                
                <!-- Target Info -->
                <div style="background: #f5f5f5; padding: 15px; border-radius: 8px; margin: 15px 0;">
                    <h3 style="margin: 0 0 10px 0; color: #333;">🎯 Profile Information</h3>
                    <p style="margin: 5px 0;"><strong>Name:</strong> {target_name}</p>
                    <p style="margin: 5px 0;"><strong>URL:</strong> <a href="{target_url}" style="color: #4CAF50;">{target_url}</a></p>
                </div>
                
                <!-- Insights -->
                <div style="margin: 20px 0;">
                    <h3 style="color: #333; margin: 0 0 15px 0;">🔍 AI Analysis Results</h3>
                    
                    {self._format_insights_section(ai_insights)}
                </div>
                
                <!-- Footer -->
                <div style="border-top: 1px solid #e0e0e0; padding-top: 20px; margin-top: 30px; text-align: center; color: #666;">
                    <p style="margin: 0; font-size: 14px;">
                        This analysis was generated by your AI-powered Monitoring Agent<br>
                        <small>Monitoring will continue automatically • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</small>
                    </p>
                </div>
                
            </div>
        </body>
        </html>
        """
        
        return html_content

    def _format_insights_section(self, insights: Dict) -> str:
        """Format insights into HTML sections"""
        html = ""
        
        insight_mappings = {
            "current_role": ("👤 Current Role", "briefcase"),
            "company": ("🏢 Company", "building"),
            "experience_level": ("📊 Experience Level", "chart"),
            "key_skills": ("🎯 Key Skills", "skills"),
            "industries": ("🏭 Industries", "industry"),
            "location": ("📍 Location", "location"),
            "engagement_score": ("💬 Engagement Score", "score"),
            "profile_completeness": ("✅ Profile Completeness", "completeness"),
            "opportunity_signals": ("🚀 Opportunity Signals", "signals")
        }
        
        for key, (title, icon) in insight_mappings.items():
            value = insights.get(key)
            if value:
                if isinstance(value, list):
                    value_text = ", ".join(str(v) for v in value[:5])  # First 5 items
                elif isinstance(value, (int, float)) and key.endswith('_score'):
                    value_text = f"{value}/10"
                else:
                    value_text = str(value)
                    
                html += f"""
                <div style="background: #f8f9fa; padding: 12px; border-left: 4px solid #4CAF50; margin: 10px 0; border-radius: 4px;">
                    <strong>{title}:</strong> {value_text}
                </div>
                """
        
        return html or "<p>No insights available at this time.</p>"

    def _generate_summary_html(self, changes_summary: List[Dict], user_name: str) -> str:
        """Generate HTML for summary email"""
        # Implementation for summary emails
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h2>📈 Monitoring Summary</h2>
            <p>Hello {user_name},</p>
            <p>Here's your monitoring summary with {len(changes_summary)} updates:</p>
            <!-- Summary content here -->
        </body>
        </html>
        """
        return html_content

    def _get_target_name(self, url: str) -> str:
        """Extract a readable name from URL"""
        try:
            if "linkedin.com/in/" in url:
                return url.split("/in/")[-1].split("/")[0].replace("-", " ").title()
            elif "linkedin.com/company/" in url:
                return url.split("/company/")[-1].split("/")[0].replace("-", " ").title()
            else:
                return url.split("//")[-1].split("/")[0]
        except:
            return "Target"

    async def _send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        """Send the actual email"""
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["From"] = f"{self.from_name} <{self.from_email}>"
            message["To"] = to_email
            message["Subject"] = subject
            
            # Add HTML content
            html_part = MIMEText(html_content, "html")
            message.attach(html_part)
            
            # Send email
            await aiosmtplib.send(
                message,
                hostname=self.smtp_host,
                port=self.smtp_port,
                start_tls=True,
                username=self.username,
                password=self.password,
            )
            
            logger.info(f"✅ Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send email to {to_email}: {e}")
            return False

    async def test_connection(self) -> bool:
        """Test SMTP connection"""
        try:
            smtp = aiosmtplib.SMTP(hostname=self.smtp_host, port=self.smtp_port)
            await smtp.connect()
            await smtp.starttls()
            await smtp.login(self.username, self.password)
            await smtp.quit()
            logger.info("✅ SMTP connection test successful")
            return True
        except Exception as e:
            logger.error(f"❌ SMTP connection test failed: {e}")
            return False