import time
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field


@dataclass
class LLMCallRecord:
    duration_seconds: float
    prompt_tokens: int | None
    completion_tokens: int | None


@dataclass
class LLMCallMetrics:
    calls: list[LLMCallRecord] = field(default_factory=list)

    @property
    def call_count(self) -> int:
        return len(self.calls)

    @property
    def total_duration_seconds(self) -> float:
        return sum(call.duration_seconds for call in self.calls)

    @property
    def total_tokens(self) -> int | None:
        if not self.calls:
            return None

        if any(
            call.prompt_tokens is None or call.completion_tokens is None
            for call in self.calls
        ):
            return None

        return sum(
            call.prompt_tokens + call.completion_tokens
            for call in self.calls
        )


_current_metrics: ContextVar[LLMCallMetrics | None] = ContextVar(
    "current_metrics", default=None
)


@contextmanager
def track_llm_metrics():
    metrics = LLMCallMetrics()
    token = _current_metrics.set(metrics)
    try:
        yield metrics
    finally:
        _current_metrics.reset(token)


def record_call(
    duration_seconds: float,
    prompt_tokens: int | None = None,
    completion_tokens: int | None = None,
) -> None:
    metrics = _current_metrics.get()

    if metrics is None:
        return

    metrics.calls.append(
        LLMCallRecord(
            duration_seconds=duration_seconds,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )
    )


@contextmanager
def timed_call():
    start = time.perf_counter()
    result = {}
    try:
        yield result
    finally:
        duration = time.perf_counter() - start
        record_call(
            duration_seconds=duration,
            prompt_tokens=result.get("prompt_tokens"),
            completion_tokens=result.get("completion_tokens"),
        )
