from dataclasses import dataclass


@dataclass
class BenchmarkContext:
    age: int
    marital_status: str
    children_count: int
    youngest_child_stage: str
    household_income: float
