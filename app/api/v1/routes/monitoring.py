from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from pydantic import BaseModel, HttpUrl

from app.modules.auth.dependencies import get_current_user
from app.modules.user.models import User
from app.modules.monitoring.services import MonitoringService
from app.modules.monitoring.models import MonitoringTarget, ChangeDetection, Snapshot

router = APIRouter(prefix="/api/v1/monitoring", tags=["monitoring"])


class CreateTargetRequest(BaseModel):
    url: HttpUrl
    target_type: str
    check_frequency: int = 3600


class UpdateTargetRequest(BaseModel):
    check_frequency: Optional[int] = None
    is_active: Optional[bool] = None


class TargetResponse(BaseModel):
    id: str
    url: str
    target_type: str
    check_frequency: int
    is_active: bool
    last_checked: Optional[str] = None
    created_at: str

    class Config:
        from_attributes = True


class ChangeResponse(BaseModel):
    id: str
    target_id: str
    change_type: str
    summary: str
    detected_at: str

    class Config:
        from_attributes = True


class SnapshotResponse(BaseModel):
    id: str
    target_id: str
    data: dict
    version: int
    created_at: str
    previous_snapshot_id: Optional[str] = None

    class Config:
        from_attributes = True


@router.post(
    "/targets", response_model=TargetResponse, status_code=status.HTTP_201_CREATED
)
async def create_monitoring_target(
    request: CreateTargetRequest, current_user: User = Depends(get_current_user)
):
    try:
        target = await MonitoringService.create_target(
            user_id=str(current_user.id),
            url=str(request.url),
            target_type=request.target_type,
            check_frequency=request.check_frequency,
        )

        return TargetResponse(
            id=str(target.id),
            url=str(target.url),
            target_type=target.target_type,
            check_frequency=target.check_frequency,
            is_active=target.is_active,
            last_checked=target.last_checked.isoformat()
            if target.last_checked
            else None,
            created_at=target.created_at.isoformat(),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/targets", response_model=List[TargetResponse])
async def get_monitoring_targets(current_user: User = Depends(get_current_user)):
    targets = await MonitoringService.get_user_targets(str(current_user.id))

    return [
        TargetResponse(
            id=str(t.id),
            url=str(t.url),
            target_type=t.target_type,
            check_frequency=t.check_frequency,
            is_active=t.is_active,
            last_checked=t.last_checked.isoformat() if t.last_checked else None,
            created_at=t.created_at.isoformat(),
        )
        for t in targets
    ]


@router.get("/targets/{target_id}", response_model=TargetResponse)
async def get_monitoring_target(
    target_id: str, current_user: User = Depends(get_current_user)
):
    target = await MonitoringService.get_target(target_id, str(current_user.id))

    if not target:
        raise HTTPException(status_code=404, detail="Target not found")

    return TargetResponse(
        id=str(target.id),
        url=str(target.url),
        target_type=target.target_type,
        check_frequency=target.check_frequency,
        is_active=target.is_active,
        last_checked=target.last_checked.isoformat() if target.last_checked else None,
        created_at=target.created_at.isoformat(),
    )


@router.patch("/targets/{target_id}", response_model=TargetResponse)
async def update_monitoring_target(
    target_id: str,
    request: UpdateTargetRequest,
    current_user: User = Depends(get_current_user),
):
    updates = request.dict(exclude_unset=True)

    target = await MonitoringService.update_target(
        target_id, str(current_user.id), **updates
    )

    if not target:
        raise HTTPException(status_code=404, detail="Target not found")

    return TargetResponse(
        id=str(target.id),
        url=str(target.url),
        target_type=target.target_type,
        check_frequency=target.check_frequency,
        is_active=target.is_active,
        last_checked=target.last_checked.isoformat() if target.last_checked else None,
        created_at=target.created_at.isoformat(),
    )


@router.delete("/targets/{target_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_monitoring_target(
    target_id: str, current_user: User = Depends(get_current_user)
):
    deleted = await MonitoringService.delete_target(target_id, str(current_user.id))

    if not deleted:
        raise HTTPException(status_code=404, detail="Target not found")


@router.get("/targets/{target_id}/changes", response_model=List[ChangeResponse])
async def get_target_changes(
    target_id: str, limit: int = 50, current_user: User = Depends(get_current_user)
):
    changes = await MonitoringService.get_target_changes(
        target_id, str(current_user.id), limit=limit
    )

    return [
        ChangeResponse(
            id=str(c.id),
            target_id=c.target_id,
            change_type=c.change_type,
            summary=c.summary,
            detected_at=c.detected_at.isoformat(),
        )
        for c in changes
    ]


@router.get("/changes", response_model=List[ChangeResponse])
async def get_all_changes(
    limit: int = 50, current_user: User = Depends(get_current_user)
):
    changes = await MonitoringService.get_user_changes(
        str(current_user.id), limit=limit
    )

    return [
        ChangeResponse(
            id=str(c.id),
            target_id=c.target_id,
            change_type=c.change_type,
            summary=c.summary,
            detected_at=c.detected_at.isoformat(),
        )
        for c in changes
    ]


@router.post("/targets/{target_id}/check")
async def trigger_target_check(
    target_id: str, current_user: User = Depends(get_current_user)
):
    result = await MonitoringService.trigger_check(target_id, str(current_user.id))

    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    return result


@router.get("/targets/{target_id}/snapshots", response_model=List[SnapshotResponse])
async def get_target_snapshots(
    target_id: str, 
    limit: int = 20, 
    current_user: User = Depends(get_current_user)
):
    target = await MonitoringService.get_target(target_id, str(current_user.id))
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    
    snapshots = await MonitoringService.get_target_snapshots(target_id, limit=limit)
    
    return [
        SnapshotResponse(
            id=str(s.id),
            target_id=s.target_id,
            data=s.data,
            version=s.version,
            created_at=s.created_at.isoformat(),
            previous_snapshot_id=s.previous_snapshot_id
        )
        for s in snapshots
    ]


@router.get("/snapshots/{snapshot_id}", response_model=SnapshotResponse)
async def get_snapshot(
    snapshot_id: str, 
    current_user: User = Depends(get_current_user)
):
    snapshot = await MonitoringService.get_snapshot(snapshot_id)
    
    if not snapshot:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    
    # Verify user owns the target this snapshot belongs to
    target = await MonitoringService.get_target(snapshot.target_id, str(current_user.id))
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    
    return SnapshotResponse(
        id=str(snapshot.id),
        target_id=snapshot.target_id,
        data=snapshot.data,
        version=snapshot.version,
        created_at=snapshot.created_at.isoformat(),
        previous_snapshot_id=snapshot.previous_snapshot_id
    )


@router.get("/snapshots/{snapshot_id}/changes")
async def get_snapshot_changes(
    snapshot_id: str,
    current_user: User = Depends(get_current_user)
):
    snapshot = await MonitoringService.get_snapshot(snapshot_id)
    
    if not snapshot:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    
    target = await MonitoringService.get_target(snapshot.target_id, str(current_user.id))
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    
    if not snapshot.previous_snapshot_id:
        return {"message": "No previous snapshot to compare with"}
    
    previous_snapshot = await MonitoringService.get_snapshot(snapshot.previous_snapshot_id)
    
    if not previous_snapshot:
        return {"message": "Previous snapshot not found"}
    
    changes = {}
    current_data = snapshot.data
    previous_data = previous_snapshot.data
    
    for key, value in current_data.items():
        if key not in previous_data:
            changes[key] = {"status": "added", "current": value, "previous": None}
        elif previous_data[key] != value:
            changes[key] = {"status": "changed", "current": value, "previous": previous_data[key]}
    
    for key, value in previous_data.items():
        if key not in current_data:
            changes[key] = {"status": "removed", "current": None, "previous": value}
    
    return {
        "snapshot_id": snapshot_id,
        "previous_snapshot_id": snapshot.previous_snapshot_id,
        "version": snapshot.version,
        "previous_version": previous_snapshot.version,
        "changes": changes,
        "total_changes": len(changes)
    }
