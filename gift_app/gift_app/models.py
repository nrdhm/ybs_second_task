import datetime as dt
import enum
from dataclasses import dataclass, field
from typing import List


class Gender(enum.Enum):
    male = enum.auto()
    female = enum.auto()


@dataclass
class Citizen:
    citizen_id: int
    town: str
    street: str
    building: str
    apartment: int
    name: str
    birth_date: dt.date
    gender: Gender
    relatives: List["Citizen"] = field(default_factory=lambda: [])
