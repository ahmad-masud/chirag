from dataclasses import dataclass, field
import time


@dataclass
class BotState:
    started_at: float = field(default_factory=time.time)
    total_responses_sent: int = 0
    channel_cooldowns: dict[int, float] = field(default_factory=dict)
    shutup_modes: dict[int, bool] = field(default_factory=dict)

    def get_uptime(self) -> str:
        seconds = int(time.time() - self.started_at)
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours}h {minutes}m {seconds}s"