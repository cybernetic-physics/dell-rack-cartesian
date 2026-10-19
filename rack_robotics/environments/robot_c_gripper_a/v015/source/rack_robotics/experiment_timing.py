"""Keep physical durations and recording cadence identical across solver rates."""
from dataclasses import dataclass
import math


@dataclass(frozen=True)
class ExperimentTiming:
    physics_hz: int = 240

    def __post_init__(self):
        if self.physics_hz not in (240,480,960):
            raise ValueError('Supported sensitivity rates are 240, 480 and 960 Hz')

    @property
    def dt(self): return 1/self.physics_hz

    @property
    def recording_stride(self): return self.physics_hz//30

    @property
    def visual_stride(self): return self.physics_hz//60

    def steps(self,seconds):
        if not math.isfinite(seconds) or seconds<0:
            raise ValueError('Duration must be finite and nonnegative')
        return round(seconds*self.physics_hz)
