from dataclasses import dataclass

@dataclass
class ApiBalance:
    total: float
    used: float
    remaining: float