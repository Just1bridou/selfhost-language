import uuid
from dataclasses import dataclass, field


class SessionNotFoundError(Exception):
    """Raised when a session id does not correspond to an active session."""


@dataclass
class Session:
    id: str
    scenario_id: str
    history: list = field(default_factory=list)


_sessions: dict[str, Session] = {}


def create_session(scenario_id: str) -> Session:
    session = Session(id=str(uuid.uuid4()), scenario_id=scenario_id)
    _sessions[session.id] = session
    return session


def get_session(session_id: str) -> Session:
    session = _sessions.get(session_id)
    if session is None:
        raise SessionNotFoundError(f"no active session with id {session_id!r}")
    return session
