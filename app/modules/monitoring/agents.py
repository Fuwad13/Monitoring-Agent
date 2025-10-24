from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage
import operator
from datetime import datetime
from .scraper import ScraperService
from .ai_service import GeminiAnalysisService
from .email_service import EmailNotificationService
from .models import MonitoringTarget, ChangeDetection, Snapshot
from app.modules.user.models import User
import difflib
import logging

logger = logging.getLogger(__name__)


class MonitoringState(TypedDict):
    target: MonitoringTarget
    scraped_data: dict
    has_changes: bool
    change_summary: str
    ai_analysis: dict
    ai_insights: dict
    user: User
    error: str | None


class MonitoringAgents:

    def __init__(self):
        self.scraper = ScraperService()
        self.ai_service = GeminiAnalysisService()
        self.email_service = EmailNotificationService()
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(MonitoringState)

        workflow.add_node("scrape", self._scrape_node)
        workflow.add_node("analyze", self._analyze_node)
        workflow.add_node("ai_analysis", self._ai_analysis_node)
        workflow.add_node("notify", self._notify_node)

        workflow.set_entry_point("scrape")
        workflow.add_edge("scrape", "analyze")
        workflow.add_edge("analyze", "ai_analysis")
        workflow.add_edge("ai_analysis", "notify")
        workflow.add_edge("notify", END)

        return workflow.compile()

    def _scrape_node(self, state: MonitoringState) -> MonitoringState:
        target = state["target"]
        logger.info(
            f"🕷️  Starting scrape for target: {target.url} (type: {target.target_type})"
        )

        try:
            logger.info(f"🔄 Initiating scraper for URL: {str(target.url)}")
            scraped_data = self.scraper.scrape_url(str(target.url), target.target_type)
            logger.info(f"✅ Scraper completed. Data keys: {list(scraped_data.keys())}")
            logger.info(f"📊 Content length: {len(scraped_data.get('content', ''))}")
            logger.info(f"🔑 Content hash: {scraped_data.get('content_hash', 'None')}")

            state["scraped_data"] = scraped_data
            state["error"] = scraped_data.get("error")

            if scraped_data.get("error"):
                logger.error(f"❌ Scraper error: {scraped_data.get('error')}")
            else:
                logger.info("✅ Scrape completed successfully")

        except Exception as e:
            logger.error(f"❌ Scraper exception: {str(e)}")
            state["error"] = str(e)
            state["scraped_data"] = {}

        return state

    def _analyze_node(self, state: MonitoringState) -> MonitoringState:
        target = state["target"]
        scraped_data = state["scraped_data"]
        logger.info(f"🔍 Starting basic analysis for target: {target.url}")

        if state.get("error") or not scraped_data:
            logger.warning(
                f"⚠️  Skipping analysis due to error or empty data. Error: {state.get('error')}"
            )
            state["has_changes"] = False
            state["ai_analysis"] = {}
            state["ai_insights"] = {}
            return state

        current_hash = scraped_data.get("content_hash")
        previous_hash = target.last_content_hash

        logger.info(f"📊 Current hash: {current_hash}")
        logger.info(f"📊 Previous hash: {previous_hash}")

        if previous_hash is None:
            logger.info("🆕 First scrape - will get AI insights")
            state["has_changes"] = False
            state["change_summary"] = "Initial snapshot - getting AI insights"
        elif current_hash != previous_hash:
            logger.info("🔄 Hash change detected - will perform AI analysis")
            state["has_changes"] = True
            state["change_summary"] = "Content changes detected"
        else:
            logger.info("✅ No hash changes detected")
            state["has_changes"] = False
            state["change_summary"] = "No changes detected"

        state["ai_analysis"] = {}
        state["ai_insights"] = {}
        return state

    async def _ai_analysis_node(self, state: MonitoringState) -> MonitoringState:
        target = state["target"]
        scraped_data = state["scraped_data"]
        logger.info(f"🤖 Starting AI analysis for target: {target.url}")

        if state.get("error") or not scraped_data:
            logger.warning("⚠️  Skipping AI analysis due to error or empty data")
            state["ai_analysis"] = {}
            state["ai_insights"] = {}
            return state

        try:
            current_content = scraped_data.get("content", "")
            
            if state["has_changes"] and target.last_content_hash:
                logger.info("🔍 Performing AI change analysis")
                previous_snapshot = None
                if target.latest_snapshot_id:
                    previous_snapshot = await Snapshot.get(target.latest_snapshot_id)
                
                previous_content = ""
                if previous_snapshot:
                    previous_content = previous_snapshot.content
                else:
                    previous_content = "No previous content available"

                ai_analysis = self.ai_service.analyze_changes(
                    old_content=previous_content,
                    new_content=current_content,
                    target_type=target.target_type
                )
                
                state["ai_analysis"] = ai_analysis
                state["has_changes"] = ai_analysis.get("has_changes", state["has_changes"])
                state["change_summary"] = ai_analysis.get("change_summary", state["change_summary"])
                
                logger.info(f"🤖 AI detected changes: {ai_analysis.get('has_changes', False)}")
                logger.info(f"📝 AI summary: {ai_analysis.get('change_summary', '')}")
                
            else:
                logger.info("📊 Extracting AI insights from content")
                ai_insights = self.ai_service.extract_profile_insights(
                    content=current_content,
                    target_type=target.target_type
                )
                state["ai_insights"] = ai_insights
                logger.info(f"💡 AI insights extracted: {len(ai_insights)} fields")

        except Exception as e:
            logger.error(f"❌ AI analysis failed: {e}")
            state["ai_analysis"] = {"error": str(e)}
            state["ai_insights"] = {}

        logger.info(f"🤖 AI analysis completed for {target.url}")
        return state

    async def _notify_node(self, state: MonitoringState) -> MonitoringState:
        logger.info("📢 Starting notification node")

        ai_analysis = state.get("ai_analysis", {})
        ai_insights = state.get("ai_insights", {})
        target = state["target"]
        user = state["user"]

        # Check user email preferences
        email_notifications_enabled = user.preferences.get("email_notifications", True)
        email_on_changes = user.preferences.get("email_on_changes", True)
        email_on_insights = user.preferences.get("email_on_insights", True)
        min_importance = user.preferences.get("min_importance_score", 5)

        if state["has_changes"] and ai_analysis:
            logger.info("🔔 Changes detected - generating AI notification")
            try:
                notification = self.ai_service.generate_notification(
                    ai_analysis=ai_analysis,
                    target_url=str(target.url)
                )
                
                # Console notification
                print(f"\n{'=' * 80}")
                print(notification["title"])
                print(f"{'=' * 80}")
                print(notification["message"])
                print(f"{'=' * 80}\n")
                
                # Email notification
                if (email_notifications_enabled and email_on_changes and 
                    ai_analysis.get("importance_score", 0) >= min_importance):
                    
                    logger.info(f"📧 Sending change email to {user.email}")
                    email_sent = await self.email_service.send_change_notification(
                        to_email=user.email,
                        target_url=str(target.url),
                        ai_analysis=ai_analysis,
                        target_type=target.target_type,
                        user_name=user.full_name
                    )
                    
                    if email_sent:
                        logger.info("✅ Change notification email sent successfully")
                    else:
                        logger.warning("⚠️ Failed to send change notification email")
                else:
                    logger.info("ℹ️ Email notification skipped (disabled or low importance)")
                
            except Exception as e:
                logger.error(f"❌ AI notification generation failed: {e}")
                # Fallback console notification
                print(f"\n{'=' * 60}")
                print("🔔 CHANGE DETECTED!")
                print(f"{'=' * 60}")
                print(f"Target: {target.url}")
                print(f"Type: {target.target_type}")
                print(f"Time: {datetime.utcnow().isoformat()}")
                print(f"Summary: {state['change_summary']}")
                print(f"{'=' * 60}\n")
                
        elif state["has_changes"]:
            logger.info("🔔 Basic change notification")
            print(f"\n{'=' * 60}")
            print("🔔 CHANGE DETECTED!")
            print(f"{'=' * 60}")
            print(f"Target: {target.url}")
            print(f"Type: {target.target_type}")
            print(f"Time: {datetime.utcnow().isoformat()}")
            print(f"Summary: {state['change_summary']}")
            print(f"{'=' * 60}\n")
            
        elif ai_insights:
            logger.info("💡 Displaying AI insights for initial scan")
            print(f"\n{'=' * 60}")
            print("💡 PROFILE INSIGHTS")
            print(f"{'=' * 60}")
            print(f"Target: {target.url}")
            if ai_insights.get("current_role"):
                print(f"Role: {ai_insights['current_role']}")
            if ai_insights.get("company"):
                print(f"Company: {ai_insights['company']}")
            if ai_insights.get("key_skills"):
                print(f"Skills: {', '.join(ai_insights['key_skills'][:5])}")
            print(f"{'=' * 60}\n")
            
            # Email insights notification
            if email_notifications_enabled and email_on_insights:
                logger.info(f"📧 Sending insights email to {user.email}")
                email_sent = await self.email_service.send_insights_notification(
                    to_email=user.email,
                    target_url=str(target.url),
                    ai_insights=ai_insights,
                    target_type=target.target_type,
                    user_name=user.full_name
                )
                
                if email_sent:
                    logger.info("✅ Insights email sent successfully")
                else:
                    logger.warning("⚠️ Failed to send insights email")
            else:
                logger.info("ℹ️ Insights email notification skipped (disabled)")
        else:
            logger.info("ℹ️ No changes or insights to notify about")

        return state

    def _generate_summary(self, target: MonitoringTarget, new_data: dict) -> str:
        return f"Content updated on {target.target_type} at {target.url}"

    async def monitor_target(self, target: MonitoringTarget) -> dict:
        logger.info(f"🚀 Starting monitoring workflow for target: {target.url}")
        logger.info(
            f"📋 Target details - ID: {target.id}, Type: {target.target_type}, User: {target.user_id}"
        )

        # Get user for email notifications
        user = await User.get(target.user_id)
        if not user:
            logger.error(f"❌ User not found: {target.user_id}")
            user = User(email="unknown@example.com", full_name="Unknown User", preferences={})

        initial_state = MonitoringState(
            target=target,
            scraped_data={},
            has_changes=False,
            change_summary="",
            ai_analysis={},
            ai_insights={},
            user=user,
            error=None,
        )

        logger.info("🔄 Executing LangGraph workflow...")
        result = await self.graph.ainvoke(initial_state)
        logger.info("✅ LangGraph workflow completed")
        logger.info(
            f"📊 Final result: has_changes={result.get('has_changes')}, error={result.get('error')}"
        )

        # Update target and save snapshots
        if result["scraped_data"]:
            logger.info("💾 Updating target with new data...")
            target.last_content_hash = result["scraped_data"].get("content_hash")
            target.last_checked = datetime.utcnow()
            
            snapshot_id = None
            if target.target_type in ["linkedin_profile", "linkedin_company"]:
                logger.info("📸 Saving LinkedIn snapshot...")
                snapshot = Snapshot(
                    target_id=str(target.id),
                    user_id=target.user_id,
                    target_type=target.target_type,
                    url=str(target.url),
                    content=result["scraped_data"].get("content", ""),
                    content_hash=result["scraped_data"].get("content_hash", ""),
                    previous_snapshot_id=target.latest_snapshot_id,
                )
                await snapshot.insert()
                snapshot_id = str(snapshot.id)
                target.latest_snapshot_id = snapshot_id
                logger.info(f"✅ Snapshot saved with ID: {snapshot_id}")
            
            await target.save()
            logger.info("✅ Target updated successfully")

            if result["has_changes"]:
                logger.info("💾 Saving change detection record...")
                change = ChangeDetection(
                    target_id=str(target.id),
                    user_id=target.user_id,
                    change_type="content_update",
                    summary=result["change_summary"],
                    before_snapshot=target.latest_snapshot_id,
                    after_snapshot=snapshot_id,
                    notified=True,
                )
                await change.save()
                logger.info("✅ Change detection record saved")
        else:
            logger.warning("⚠️  No scraped data to save - skipping target update")

        logger.info(f"🏁 Monitoring workflow completed for {target.url}")
        return result
    
    def cleanup(self):
        logger.info("🧹 Cleaning up monitoring agent resources")
        if hasattr(self.scraper, 'linkedin_service') and self.scraper.linkedin_service:
            self.scraper.linkedin_service.cleanup()
    
    def __del__(self):
        try:
            self.cleanup()
        except Exception:
            pass
