from celery import shared_task
from app.core.db import database
from app.modules.monitoring.models import MonitoringTarget
from app.modules.monitoring.agents import MonitoringAgents
from datetime import datetime, timedelta
import asyncio
import logging

logger = logging.getLogger(__name__)


@shared_task(name="app.modules.monitoring.tasks.check_all_targets")
def check_all_targets():
    return asyncio.run(_check_all_targets_async())


async def _check_all_targets_async():
    await database.connect()

    agents = MonitoringAgents()

    targets = await MonitoringTarget.find({"is_active": True}).to_list()

    checked_count = 0
    for target in targets:
        if (
            target.last_checked is None
            or (datetime.utcnow() - target.last_checked).total_seconds()
            >= target.check_frequency
        ):
            try:
                await agents.monitor_target(target)
                checked_count += 1
            except Exception as e:
                print(f"Error checking target {target.url}: {e}")

    print(f"✅ Checked {checked_count} targets")
    return checked_count


@shared_task(name="app.modules.monitoring.tasks.check_single_target")
def check_single_target(target_id: str):
    logger.info(f"🎯 Starting single target check for ID: {target_id}")
    result = asyncio.run(_check_single_target_async(target_id))
    logger.info(f"✅ Single target check completed. Result: {result}")
    return result


async def _check_single_target_async(target_id: str):
    """Async function to check single target"""
    logger.info(f"🔍 Connecting to database for target: {target_id}")
    await database.connect()

    logger.info(f"📋 Fetching target from database: {target_id}")
    target = await MonitoringTarget.get(target_id)
    if not target:
        logger.error(f"❌ Target not found: {target_id}")
        return {"error": "Target not found", "target_id": target_id}

    logger.info(f"🤖 Starting monitoring agents for target: {target.url}")
    agents = MonitoringAgents()
    result = await agents.monitor_target(target)

    final_result = {
        "target_id": target_id,
        "checked": True,
        "has_changes": result.get("has_changes", False),
        "error": result.get("error"),
        "change_summary": result.get("change_summary", ""),
    }

    logger.info(f"📊 Task result: {final_result}")
    return final_result
