from dataclasses import dataclass
from typing import Any, Dict, List, Literal

@dataclass
class Problem(Exception):
    content: str = "An internal server error occurred. Please report this issue to support."
    status: int = 500