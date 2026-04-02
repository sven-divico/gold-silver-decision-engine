from typing import Protocol


class RatioSignalInput(Protocol):
    ratio: float
    status: str


def classify_ratio(ratio: float) -> str:
    if ratio > 80:
        return "elevated"
    if ratio < 60:
        return "compressed"
    return "neutral"


def ratio_signal_text(result: RatioSignalInput) -> str:
    return f"The gold/silver ratio is {result.status} at {result.ratio:.2f}."
