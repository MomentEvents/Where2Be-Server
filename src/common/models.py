from dataclasses import dataclass
from typing import Any, Dict, List
from typing_extensions import Literal

@dataclass
class Problem(Exception):
    content: str = "An internal server error occurred. Please report this issue to support."
    status: int = 500