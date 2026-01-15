from typing import Dict
from pydantic import BaseModel


class Competitor(BaseModel):
    RacerID: str
    Number: str
    Transponder: str
    FirstName: str
    LastName: str
    Nationality: str
    AdditionalData: str
    ClassID: str
    Position: str
    Laps: str
    TotalTime: str
    BestPosition: str
    BestLap: str
    BestLapTime: str
    LastLapTime: str


class Lap(BaseModel):
    Lap: str
    Position: str
    LapTime: str
    FlagStatus: str
    TotalTime: str


class Details(BaseModel):
    Competitor: Competitor
    Laps: List[Lap]


class ApiResponse(BaseModel):
    Successful: bool
    Details: Details


class RaceClass(BaseModel):
    ClassID: str
    Description: str


class Session(BaseModel):
    RunNumber: str
    SessionName: str
    TrackName: str
    TrackLength: str
    CurrentTime: str
    SessionTime: str
    TimeToGo: str
    LapsToGo: str
    FlagStatus: str
    SortMode: str
    Classes: Dict[str, RaceClass]
    Competitors: Dict[str, Competitor]


class SessionResponse(BaseModel):
    Successful: bool
    Session: Session
