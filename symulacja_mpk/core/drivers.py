from abc import ABC, abstractmethod

class Driver(ABC):  # abstrakcyjna klasa kierowcy danego pojazdu - ma imię i wypłatę
    def __init__(self, name: str, salary: float):
        self.name = name
        self.salary = salary

    @abstractmethod
    def get_speed_multiplier(self) -> float:
        pass

    @abstractmethod
    def get_failure_risk_multiplier(self) -> float:
        pass

class NormalDriver(Driver): # bazowa prędkość i ryzyko awarii
    def __init__(self, name: str, salary: float):
        super().__init__(name, salary)

    def get_speed_multiplier(self) -> float:
        return 1.0

    def get_failure_risk_multiplier(self) -> float:
        return 1.0


class CarefulDriver(Driver): # wolniejszy-mniejsze ryzyko
    def __init__(self, name: str, salary: float):
        super().__init__(name, salary)

    def get_speed_multiplier(self) -> float:
        return 0.8

    def get_failure_risk_multiplier(self) -> float:
        return 0.5


class AggressiveDriver(Driver): # szybszy-większe ryzyko
    def __init__(self, name: str, salary: float):
        super().__init__(name, salary)

    def get_speed_multiplier(self) -> float:
        return 1.2

    def get_failure_risk_multiplier(self) -> float:
        return 3