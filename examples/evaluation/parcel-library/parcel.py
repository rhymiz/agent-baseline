from dataclasses import dataclass
from enum import Enum


class State(Enum):
    QUEUED = "queued"
    COMPLETED = "completed"


@dataclass(frozen=True)
class Parcel:
    identifier: str
    state: State


def complete(parcel: Parcel) -> Parcel:
    if parcel.state is not State.QUEUED:
        raise ValueError("Only queued parcels can be completed")
    return Parcel(parcel.identifier, State.COMPLETED)
