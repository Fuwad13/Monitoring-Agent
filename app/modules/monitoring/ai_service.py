import json
import logging
from typing import Dict, Optional
import google.generativeai as genai
from app.core.config import settings

logger = logging.getLogger(__name__)


class GeminiAnalysisService:
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(
            model_name=settings.GEMINI_MODEL,
            generation_config={
                "temperature": settings.GEMINI_TEMPERATURE,
                "top_p": 0.95,
                "top_k": 64,
                "max_output_tokens": 8192,
                "response_mime_type": "application/json",
            }
        )
        logger.info(f"🤖 Gemini AI service initialized with model: {settings.GEMINI_MODEL}")

    def analyze_changes(self, old_content: str, new_content: str, target_type: str) -> Dict:
        """Analyze changes between old and new content using Gemini"""
        logger.info("🔍 Starting Gemini change analysis")
        
        if target_type in ["linkedin_profile", "linkedin_company"]:
            return self._analyze_linkedin_changes(old_content, new_content, target_type)
        else:
            return self._analyze_website_changes(old_content, new_content)

    def _analyze_linkedin_changes(self, old_content: str, new_content: str, target_type: str) -> Dict:
        """Analyze LinkedIn profile or company changes"""
        content_type = "profile" if target_type == "linkedin_profile" else "company"
        
        prompt = f"""
        Analyze the changes between these two LinkedIn {content_type} contents and provide detailed insights.

        OLD CONTENT:
        {old_content[:4000]}

        NEW CONTENT:
        {new_content[:4000]}

        Please analyze and return a JSON response with the following structure:
        {{
            "has_changes": true/false,
            "change_summary": "Brief description of what changed",
            "change_categories": ["job", "skills", "experience", "education", "contact", "company_info"],
            "importance_score": 1-10,
            "key_changes": [
                {{
                    "category": "job/skills/etc",
                    "old_value": "previous value",
                    "new_value": "new value",
                    "description": "what this change means"
                }}
            ],
            "insights": {{
                "career_movement": "description of career progression",
                "skill_development": "new skills or expertise gained",
                "engagement_potential": "likelihood of being open to opportunities",
                "notable_updates": "any standout changes worth mentioning"
            }},
            "alert_priority": "low/medium/high",
            "suggested_action": "recommended follow-up action"
        }}

        If no meaningful changes detected, set has_changes to false and provide minimal response.
        """

        try:
            response = self.model.generate_content(prompt)
            result = json.loads(response.text)
            logger.info(f"✅ Gemini analysis completed. Changes detected: {result.get('has_changes', False)}")
            return result
        except Exception as e:
            logger.error(f"❌ Gemini analysis failed: {e}")
            return {
                "has_changes": False,
                "change_summary": f"AI analysis failed: {str(e)}",
                "change_categories": [],
                "importance_score": 1,
                "key_changes": [],
                "insights": {},
                "alert_priority": "low",
                "suggested_action": "Manual review required"
            }

    def _analyze_website_changes(self, old_content: str, new_content: str) -> Dict:
        """Analyze general website changes"""
        prompt = f"""
        Analyze the changes between these two website contents:

        OLD CONTENT:
        {old_content[:4000]}

        NEW CONTENT:
        {new_content[:4000]}

        Return JSON with:
        {{
            "has_changes": true/false,
            "change_summary": "what changed",
            "change_type": "content/structure/data",
            "importance_score": 1-10,
            "key_changes": ["list of main changes"],
            "alert_priority": "low/medium/high"
        }}
        """

        try:
            response = self.model.generate_content(prompt)
            result = json.loads(response.text)
            logger.info(f"✅ Website analysis completed. Changes: {result.get('has_changes', False)}")
            return result
        except Exception as e:
            logger.error(f"❌ Website analysis failed: {e}")
            return {
                "has_changes": False,
                "change_summary": f"AI analysis failed: {str(e)}",
                "change_type": "unknown",
                "importance_score": 1,
                "key_changes": [],
                "alert_priority": "low"
            }

    def generate_notification(self, ai_analysis: Dict, target_url: str) -> Dict:
        """Generate human-readable notification from AI analysis"""
        if not ai_analysis.get("has_changes", False):
            return {
                "title": "No Changes Detected",
                "message": f"No significant changes found for {target_url}",
                "priority": "low"
            }

        insights = ai_analysis.get("insights", {})
        key_changes = ai_analysis.get("key_changes", [])
        
        # Create formatted notification
        changes_text = []
        for change in key_changes[:3]:  # Top 3 changes
            if change.get("category") and change.get("description"):
                changes_text.append(f"• {change['category'].title()}: {change['description']}")
        
        changes_summary = "\n".join(changes_text) if changes_text else ai_analysis.get("change_summary", "")
        
        priority_emoji = {
            "high": "🔥",
            "medium": "⚡", 
            "low": "📊"
        }
        
        priority = ai_analysis.get("alert_priority", "low")
        emoji = priority_emoji.get(priority, "📊")
        
        title = f"{emoji} {priority.upper()} PRIORITY UPDATE"
        
        message = f"""
{title}
🎯 Target: {target_url}
📋 Summary: {ai_analysis.get('change_summary', 'Changes detected')}

🔍 Key Changes:
{changes_summary}

💡 Insights:
{insights.get('career_movement', insights.get('notable_updates', 'Analysis completed'))}

⭐ Importance: {ai_analysis.get('importance_score', 1)}/10
🎯 Action: {ai_analysis.get('suggested_action', 'Monitor for further changes')}
        """.strip()

        return {
            "title": title,
            "message": message,
            "priority": priority,
            "importance_score": ai_analysis.get("importance_score", 1)
        }

    def extract_profile_insights(self, content: str, target_type: str) -> Dict:
        """Extract key insights from profile content for intelligence"""
        if target_type not in ["linkedin_profile", "linkedin_company"]:
            return {}
            
        content_type = "profile" if target_type == "linkedin_profile" else "company"
        
        prompt = f"""
        Extract key insights from this LinkedIn {content_type}:

        CONTENT:
        {content[:4000]}

        Return JSON with:
        {{
            "current_role": "current position/title",
            "company": "current company",
            "experience_level": "junior/mid/senior/executive",
            "key_skills": ["skill1", "skill2", "skill3"],
            "industries": ["industry1", "industry2"],
            "location": "city, country",
            "recent_activity": "description of recent updates",
            "engagement_score": 1-10,
            "profile_completeness": 1-10,
            "opportunity_signals": ["signal1", "signal2"]
        }}
        """

        try:
            response = self.model.generate_content(prompt)
            result = json.loads(response.text)
            logger.info("✅ Profile insights extracted successfully")
            return result
        except Exception as e:
            logger.error(f"❌ Profile insight extraction failed: {e}")
            return {}