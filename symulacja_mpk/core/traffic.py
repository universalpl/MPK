from enum import Enum

class TimePeriod(Enum):  # pory dnia - względem nich są opóźnienia/korki
    MORNING = 1
    MIDDAY = 2
    AFTERNOON = 3
    EVENING = 4


class Traffic:  # warunki ruchu drogowego
    def __init__(self, intensity: int, period: TimePeriod):
        self._intensity = intensity
        self._period = period

    def get_delay_factor(self) -> float:  # współczynnik opóźnienia; im większe niż 1.0, tym większe opóźnienie przez intensywność trasy
        return 1 + (self._intensity / 10)