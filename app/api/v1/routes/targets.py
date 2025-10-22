from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, status, Query
from beanie import PydanticObjectId

from app.core.log import get_logger
from app.core.config import settings
from app.modules.auth.dependencies import get_current_user
from app.modules.user.models import User
from app.modules.monitoring.models import (
    Target,
    TargetCreate,
    TargetUpdate,
    TargetResponse,
    Change,
    ChangeResponse,
)
from app.tasks.monitoring import trigger_target_monitoring

logger = get_logger(__name__, settings.LOG_FILE_PATH)

router = APIRouter(prefix="/api/v1/targets", tags=["targets"])


@router.post("", response_model=TargetResponse, status_code=status.HTTP_201_CREATED)
async def create_target(
    target_data: TargetCreate, current_user: User = Depends(get_current_user)
):
    """Create a new monitoring target"""
    try:
        logger.info(
            f"Creating target for user {current_user.username}: {target_data.url}"
        )

        # Check if target already exists for this user
        existing_target = await Target.find_one(
            {"user_id": str(current_user.id), "url": target_data.url}
        )

        if existing_target:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Target URL already exists for this user",
            )

        # Validate target type
        valid_types = ["linkedin_profile", "linkedin_company", "website"]
        if target_data.target_type not in valid_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid target type. Must be one of: {', '.join(valid_types)}",
            )

        # Create new target
        target = Target(
            url=target_data.url,
            target_type=target_data.target_type,
            user_id=str(current_user.id),
            monitoring_frequency=target_data.monitoring_frequency,
            xpath_selectors=target_data.xpath_selectors,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        await target.insert()

        logger.info(f"Target created successfully: {target.id}")

        return TargetResponse(
            id=str(target.id),
            url=target.url,
            target_type=target.target_type,
            monitoring_frequency=target.monitoring_frequency,
            last_checked=target.last_checked,
            is_active=target.is_active,
            created_at=target.created_at,
            updated_at=target.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating target: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create target",
        )


@router.get("", response_model=List[TargetResponse])
async def list_targets(
    current_user: User = Depends(get_current_user),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    target_type: Optional[str] = Query(None, description="Filter by target type"),
    limit: int = Query(50, le=100, description="Maximum number of targets to return"),
    skip: int = Query(0, ge=0, description="Number of targets to skip"),
):
    """List user's monitoring targets"""
    try:
        logger.info(f"Listing targets for user {current_user.username}")

        # Build query filters
        query_filter = {"user_id": str(current_user.id)}

        if is_active is not None:
            query_filter["is_active"] = is_active

        if target_type:
            query_filter["target_type"] = target_type

        # Get targets with pagination
        targets = await Target.find(query_filter).skip(skip).limit(limit).to_list()

        logger.info(f"Found {len(targets)} targets for user {current_user.username}")

        return [
            TargetResponse(
                id=str(target.id),
                url=target.url,
                target_type=target.target_type,
                monitoring_frequency=target.monitoring_frequency,
                last_checked=target.last_checked,
                is_active=target.is_active,
                created_at=target.created_at,
                updated_at=target.updated_at,
            )
            for target in targets
        ]

    except Exception as e:
        logger.error(f"Error listing targets: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve targets",
        )


@router.get("/{target_id}", response_model=TargetResponse)
async def get_target(target_id: str, current_user: User = Depends(get_current_user)):
    """Get a specific target by ID"""
    try:
        logger.info(f"Getting target {target_id} for user {current_user.username}")

        # Find target
        target = await Target.find_one(
            {"_id": PydanticObjectId(target_id), "user_id": str(current_user.id)}
        )

        if not target:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Target not found"
            )

        return TargetResponse(
            id=str(target.id),
            url=target.url,
            target_type=target.target_type,
            monitoring_frequency=target.monitoring_frequency,
            last_checked=target.last_checked,
            is_active=target.is_active,
            created_at=target.created_at,
            updated_at=target.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting target: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve target",
        )


@router.put("/{target_id}", response_model=TargetResponse)
async def update_target(
    target_id: str,
    target_data: TargetUpdate,
    current_user: User = Depends(get_current_user),
):
    """Update a target's configuration"""
    try:
        logger.info(f"Updating target {target_id} for user {current_user.username}")

        # Find target
        target = await Target.find_one(
            {"_id": PydanticObjectId(target_id), "user_id": str(current_user.id)}
        )

        if not target:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Target not found"
            )

        # Update fields if provided
        update_data = {}
        if target_data.monitoring_frequency is not None:
            update_data["monitoring_frequency"] = target_data.monitoring_frequency
        if target_data.is_active is not None:
            update_data["is_active"] = target_data.is_active
        if target_data.xpath_selectors is not None:
            update_data["xpath_selectors"] = target_data.xpath_selectors

        # Always update the updated_at timestamp
        update_data["updated_at"] = datetime.now(timezone.utc)

        # Apply updates
        await target.update({"$set": update_data})

        # Refresh target from database
        updated_target = await Target.get(target.id)

        logger.info(f"Target {target_id} updated successfully")

        return TargetResponse(
            id=str(updated_target.id),
            url=updated_target.url,
            target_type=updated_target.target_type,
            monitoring_frequency=updated_target.monitoring_frequency,
            last_checked=updated_target.last_checked,
            is_active=updated_target.is_active,
            created_at=updated_target.created_at,
            updated_at=updated_target.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating target: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update target",
        )


@router.delete("/{target_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_target(target_id: str, current_user: User = Depends(get_current_user)):
    """Delete a monitoring target"""
    try:
        logger.info(f"Deleting target {target_id} for user {current_user.username}")

        # Find target
        target = await Target.find_one(
            {"_id": PydanticObjectId(target_id), "user_id": str(current_user.id)}
        )

        if not target:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Target not found"
            )

        # Delete the target
        await target.delete()

        logger.info(f"Target {target_id} deleted successfully")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting target: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete target",
        )


@router.get("/{target_id}/changes", response_model=List[ChangeResponse])
async def get_target_changes(
    target_id: str,
    current_user: User = Depends(get_current_user),
    limit: int = Query(20, le=100, description="Maximum number of changes to return"),
    skip: int = Query(0, ge=0, description="Number of changes to skip"),
):
    """Get change history for a specific target"""
    try:
        logger.info(f"Getting changes for target {target_id}")

        # Verify target ownership
        target = await Target.find_one(
            {"_id": PydanticObjectId(target_id), "user_id": str(current_user.id)}
        )

        if not target:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Target not found"
            )

        # Get changes for this target
        changes = (
            await Change.find({"target_id": target_id})
            .sort([("timestamp", -1)])
            .skip(skip)
            .limit(limit)
            .to_list()
        )

        logger.info(f"Found {len(changes)} changes for target {target_id}")

        return [
            ChangeResponse(
                id=str(change.id),
                target_id=change.target_id,
                change_type=change.change_type,
                summary=change.summary,
                confidence_score=change.confidence_score,
                timestamp=change.timestamp,
                notification_sent=change.notification_sent,
            )
            for change in changes
        ]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting target changes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve changes",
        )


@router.post("/{target_id}/test", response_model=dict)
async def test_target_scraping(
    target_id: str, current_user: User = Depends(get_current_user)
):
    """Test scraping a target (placeholder for now)"""
    try:
        logger.info(f"Testing target {target_id} for user {current_user.username}")

        # Verify target ownership
        target = await Target.find_one(
            {"_id": PydanticObjectId(target_id), "user_id": str(current_user.id)}
        )

        if not target:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Target not found"
            )

        # Trigger monitoring task for this target
        task_result = trigger_target_monitoring.delay(target_id)

        logger.info(f"Target {target_id} monitoring task triggered: {task_result.id}")

        return {
            "message": "Target monitoring triggered successfully",
            "target_id": target_id,
            "url": target.url,
            "target_type": target.target_type,
            "task_id": task_result.id,
            "status": "triggered",
            "note": "Check task status using the returned task_id",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing target: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to test target",
        )
