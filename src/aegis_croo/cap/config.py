import os
from typing import Literal


CAPMode = Literal["mock", "real"]
CAP_MODE: CAPMode = "mock"


def configured_cap_mode() -> CAPMode:
    mode = os.getenv("CAP_MODE", CAP_MODE).strip().lower()
    if mode == "real":
        return "real"
    return "mock"
