from typing import List, Optional
from bson import ObjectId
from .models import MonitoringTarget, ChangeDetection, Snapshot
from app.core.celery_app import celery_app


class MonitoringService:

    @staticmethod
    async def create_target(
        user_id: str, url: str, target_type: str, check_frequency: int = 3600
    ) -> MonitoringTarget:

        existing = await MonitoringTarget.find_one(
            MonitoringTarget.user_id == user_id, MonitoringTarget.url == url
        )

        if existing:
            raise ValueError("Target already exists for this user")

        target = MonitoringTarget(
            user_id=user_id,
            url=url,
            target_type=target_type,
            check_frequency=check_frequency,
            is_active=True,
        )

        await target.insert()

        try:
            celery_app.send_task(
                "app.modules.monitoring.tasks.check_single_target",
                args=[str(target.id)],
            )
        except Exception as e:
            print(
                f"Warning: Could not trigger immediate check for target {target.id}: {e}"
            )

        return target

    @staticmethod
    async def get_user_targets(user_id: str) -> List[MonitoringTarget]:
        targets = await MonitoringTarget.find(
            MonitoringTarget.user_id == user_id
        ).to_list()
        return targets

    @staticmethod
    async def get_target(target_id: str, user_id: str) -> Optional[MonitoringTarget]:
        target = await MonitoringTarget.get(target_id)
        if target and target.user_id == user_id:
            return target
        return None

    @staticmethod
    async def update_target(
        target_id: str, user_id: str, **updates
    ) -> Optional[MonitoringTarget]:
        target = await MonitoringTarget.get(target_id)

        if not target or target.user_id != user_id:
            return None

        allowed_fields = {"check_frequency", "is_active"}
        for key, value in updates.items():
            if key in allowed_fields:
                setattr(target, key, value)

        await target.save()
        return target

    @staticmethod
    async def delete_target(target_id: str, user_id: str) -> bool:
        target = await MonitoringTarget.get(target_id)

        if not target or target.user_id != user_id:
            return False

        await target.delete()
        return True

    @staticmethod
    async def get_target_changes(
        target_id: str, user_id: str, limit: int = 50
    ) -> List[ChangeDetection]:
        changes = (
            await ChangeDetection.find(
                ChangeDetection.target_id == target_id,
                ChangeDetection.user_id == user_id,
            )
            .sort(-ChangeDetection.detected_at)
            .limit(limit)
            .to_list()
        )

        return changes

    @staticmethod
    async def get_user_changes(user_id: str, limit: int = 50) -> List[ChangeDetection]:
        changes = (
            await ChangeDetection.find(ChangeDetection.user_id == user_id)
            .sort(-ChangeDetection.detected_at)
            .limit(limit)
            .to_list()
        )

        return changes

    @staticmethod
    async def trigger_check(target_id: str, user_id: str) -> dict:
        target = await MonitoringTarget.get(target_id)

        if not target or target.user_id != user_id:
            return {"error": "Target not found"}

        try:
            celery_app.send_task(
                "app.modules.monitoring.tasks.check_single_target", args=[target_id]
            )
            return {"message": "Check triggered", "target_id": target_id}
        except Exception as e:
            return {
                "error": f"Could not trigger check: {str(e)}",
                "target_id": target_id,
            }

    @staticmethod
    async def get_target_snapshots(target_id: str, limit: int = 10) -> List[Snapshot]:
        snapshots = await Snapshot.find(
            {"target_id": target_id}
        ).sort([("created_at", -1)]).limit(limit).to_list()
        return snapshots

    @staticmethod
    async def get_snapshot(snapshot_id: str) -> Optional[Snapshot]:
        snapshot = await Snapshot.find_one({"_id": ObjectId(snapshot_id)})
        return snapshot
