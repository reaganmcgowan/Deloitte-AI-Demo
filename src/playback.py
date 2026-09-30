"""A monotonic presentation clock; smooth synthetic measurements with checkpoint pauses."""
from dataclasses import dataclass

CHECKPOINT_MINUTES = (0, 60, 120, 150, 180)
PAUSE_REASONS = {
    1: "Baseline ready. Start the day to watch conditions develop.",
    2: "New finding: C-184 grid strain is elevated as demand rises.",
    3: "Escalation: C-184 grid strain is now high. Inspection is proposed.",
    4: "Weather alert: strong wind and low humidity. No electrical anomaly yet.",
    5: "Critical incident: T-882 anomaly combines with dangerous fire weather. Review the evidence.",
}


@dataclass
class Playback:
    checkpoint: int = 1
    minutes: float = 0.0
    running: bool = False
    last_tick: float | None = None
    minutes_per_second: float = 6.0

    @classmethod
    def at_stage(cls, stage: int) -> "Playback":
        return cls(checkpoint=stage, minutes=float(CHECKPOINT_MINUTES[stage - 1]))

    @property
    def finished(self) -> bool:
        return self.checkpoint == 5

    @property
    def time_label(self) -> str:
        total = 13 * 60 + int(self.minutes)
        return f"{(total // 60) % 12 or 12}:{total % 60:02d} PM"

    def seek(self, minute: float) -> None:
        if not 0 <= minute <= 180:
            raise ValueError("Time must be between 0 and 180 minutes")
        self.pause()
        self.minutes = float(minute)
        self.checkpoint = max(i + 1 for i, value in enumerate(CHECKPOINT_MINUTES) if value <= minute)

    def resume(self, now: float) -> None:
        if not self.finished and not self.running:
            self.running, self.last_tick = True, now

    def pause(self) -> None:
        self.running, self.last_tick = False, None

    def tick(self, now: float) -> bool:
        """Return True once at the next checkpoint; discard overshoot, never skip pauses."""
        if not self.running or self.last_tick is None or self.finished:
            return False
        elapsed = max(0.0, now - self.last_tick)
        self.last_tick = max(now, self.last_tick)
        target = CHECKPOINT_MINUTES[self.checkpoint]
        self.minutes = min(float(target), self.minutes + elapsed * self.minutes_per_second)
        if self.minutes >= target:
            self.checkpoint += 1
            self.pause()
            return True
        return False
