from enum import StrEnum


class Decision(StrEnum):
    BLOCK = "BLOCK"
    WAIT = "WAIT"
    EXECUTE = "EXECUTE"


class Confidence(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
