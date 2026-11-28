
from app.schemas.transport import TransportStop


MOCK_STOPS = [
    TransportStop(
        stop_id="mock-001",
        name="Stephansplatz",
        latitude=48.2083,
        longitude=16.3731,
        modes=["metro"],
    ),
    TransportStop(
        stop_id="mock-002",
        name="Karlsplatz",
        latitude=48.2005,
        longitude=16.3695,
        modes=["metro"],
    ),
    TransportStop(
        stop_id="mock-003",
        name="Schottentor",
        latitude=48.2156,
        longitude=16.3627,
        modes=["tram"],
    ),
]


def get_stops(
    mode: str | None = None,
    search: str | None = None,
) -> list[TransportStop]:
    stops = MOCK_STOPS.copy()

    if mode:
        stops = [
            stop for stop in stops
            if mode.lower() in stop.modes
        ]

    if search:
        stops = [
            stop for stop in stops
            if search.strip().lower() in stop.name.lower()
        ]

    return stops


def get_stop_by_id(stop_id: str) -> TransportStop | None:
    return next(
        (
            stop for stop in MOCK_STOPS
            if stop.stop_id == stop_id
        ),
        None,
    )
