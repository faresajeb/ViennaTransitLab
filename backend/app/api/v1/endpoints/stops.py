
from fastapi import APIRouter, HTTPException, Query

from app.schemas.transport import TransportStop
from app.services.stop_service import get_stops, get_stop_by_id


router = APIRouter(tags=["Transport Stops"])


@router.get("/stops", response_model=list[TransportStop])
def list_stops(
    mode: str | None = Query(default=None, min_length=1),
    search: str | None = Query(default=None, max_length=100),
):
    return get_stops(mode=mode, search=search)


@router.get("/stops/{stop_id}", response_model=TransportStop)
def retrieve_stop(stop_id: str):
    stop = get_stop_by_id(stop_id)

    if stop is None:
        raise HTTPException(
            status_code=404,
            detail="Transport stop not found",
        )

    return stop
