import unittest
import random

from enum import Enum

# Mockowane komponenty z oryginalnego kodu-komentarze w poszczególnych klasach

class TimePeriod(Enum):
    MORNING = 1
    MIDDAY = 2
    AFTERNOON = 3
    EVENING = 4

class Traffic:
    def __init__(self, intensity: int, period: TimePeriod):
        self._intensity = intensity
        self._period = period

    def get_delay_factor(self) -> float:
        return 1 + (self._intensity / 10)

class Route:
    def __init__(self, stops, length: float, traffic: Traffic):
        self._stops = stops
        self._length = length
        self._traffic = traffic

    def get_delay_factor(self) -> float:
        return self._traffic.get_delay_factor()

    def get_stops(self):
        return self._stops

    def get_length(self):
        return self._length

    def get_stop_positions(self):
        return [50 + i * 100 for i in range(len(self._stops))]

class Driver:
    def __init__(self, name: str, salary: float):
        self.name = name
        self.salary = salary

    def get_speed_multiplier(self) -> float:
        return 1.0

    def get_failure_risk_multiplier(self) -> float:
        return 1.0

class Vehicle:
    def __init__(self, line_number, route, driver, speed=1.0):
        self.line_number = line_number
        self.route = route
        self.driver = driver
        self.base_speed = speed
        self.speed = speed * driver.get_speed_multiplier()
        self.state = "Good"
        self.condition = 10
        self.repair_duration = 0.0
        self.x = 50
        self.direction = 1
        self.y = 0
        self.hours_driven = 0.0
        self.time_broken = 0.0
        self.wait_timer = 0.0
        self.stop_positions = route.get_stop_positions()
        self.next_stop_index = 0
        self.active = True
        self.breakdown_duration = 0.0
        self.activation_time = 0

    def update(self, dt, delay_factor, current_time):
        if not self.active:
            if current_time >= self.activation_time:
                self.active = True
            else:
                return

        if self.state == "Broken":
            self.time_broken += dt / 1000.0
            if self.time_broken < self.breakdown_duration + self.repair_duration:
                return
            self.state = "Good"
            self.condition = 10
            self.time_broken = 0
            return

        if self.wait_timer > 0:
            self.wait_timer -= dt / 1000.0
            return

        self.x += self.direction * (self.speed / delay_factor)

        if self.next_stop_index < len(self.stop_positions):
            stop_x = self.stop_positions[self.next_stop_index]
            if abs(self.x - stop_x) < 2:
                self.wait_timer = 5.0
                self.next_stop_index += 1

    def calculate_cost(self):
        raise NotImplementedError()

class Bus(Vehicle):
    def __init__(self, line_number, route, driver, fuel_consumption, speed=1.0):
        super().__init__(line_number, route, driver, speed)
        self.fuel_consumption = fuel_consumption

    def calculate_cost(self):
        return self.fuel_consumption * self.route.get_length() + self.driver.salary

class Tram(Vehicle):
    def __init__(self, line_number, route, driver, electricity_consumption, speed=1.0):
        super().__init__(line_number, route, driver, speed)
        self.electricity_consumption = electricity_consumption

    def calculate_cost(self):
        return self.electricity_consumption * self.route.get_length() + self.driver.salary

class Maintenance:
    def __init__(self, base_failure_chance_per_second=1.0):  # 100% szansy na testach
        self.base_failure_chance = base_failure_chance_per_second

    def check_failure(self, vehicle: Vehicle, dt):
        if vehicle.condition > 0:
            risk_multiplier = 11 - vehicle.condition
            failure_chance = self.base_failure_chance * risk_multiplier
            if random.random() < failure_chance * (dt / 1000.0):
                vehicle.condition -= 1
                if vehicle.condition <= 0:
                    vehicle.state = "Broken"
                    vehicle.breakdown_duration = 5
                    vehicle.repair_duration = 10
                    vehicle.time_broken = 0


# Testy

class TestVehicleOperations(unittest.TestCase): # sprawdzanie, czy koszt operacyjny dla pojazdów jest poprawny oraz wszelakie warunku na przystankach, awarii

    def test_bus_cost(self): # test dla autobusu-sprawdza koszt operacyjny
        route = Route(["A", "B"], 10, Traffic(3, TimePeriod.MORNING))
        driver = Driver("Kowalski", 2000)
        bus = Bus("B1", route, driver, fuel_consumption=0.4)
        self.assertEqual(bus.calculate_cost(), 0.4 * 10 + 2000)

    def test_tram_cost(self): # test dla tramwaju-sprawdza koszt operacyjny
        route = Route(["A", "B", "C"], 8, Traffic(5, TimePeriod.EVENING))
        driver = Driver("Nowak", 2500)
        tram = Tram("T1", route, driver, electricity_consumption=0.5)
        self.assertEqual(tram.calculate_cost(), 0.5 * 8 + 2500)

    def test_maintenance_breakdown(self): # Sprawdza test, czy mechanizm awarii działa z założeniami oraz ustawia warunki na nowo i sprawdza stan pojazdu
        route = Route(["A", "B"], 10, Traffic(2, TimePeriod.AFTERNOON))
        driver = Driver("Testowy", 2000)
        bus = Bus("B2", route, driver, fuel_consumption=0.3)
        bus.condition = 1  # zła kondycja

        maintenance = Maintenance(base_failure_chance_per_second=1.0)  # gwarantowana awaria
        random.seed(0)  # powtarzalność testu
        maintenance.check_failure(bus, 1000)

        self.assertEqual(bus.state, "Broken")
        self.assertGreater(bus.breakdown_duration, 0)

    def test_vehicle_stops_and_waits(self): # sprawdza, czy dobrze zatrzymuje się na przystanku i liczy czas postoju
        route = Route(["A", "B"], 10, Traffic(0, TimePeriod.MORNING))
        driver = Driver("Test", 1000)
        bus = Bus("B3", route, driver, 0.2)
        bus.x = 149  # prawie na przystanku (przy 150)
        bus.stop_positions = [150, 250]
        bus.speed = 1.0

        bus.update(dt=100, delay_factor=1.0, current_time=10) # symulacja dojazdu
        self.assertEqual(bus.wait_timer, 5.0)  # czy zaczął się postój?
        bus.update(dt=5000, delay_factor=1.0, current_time=15)  # symulacja czasu postoju
        self.assertLessEqual(bus.wait_timer, 0) # czy postój się zakończył?


if __name__ == "__main__":
    unittest.main()