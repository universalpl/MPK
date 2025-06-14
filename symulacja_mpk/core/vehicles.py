from abc import ABC, abstractmethod
import pygame
from symulacja_mpk.core.route import Route
from symulacja_mpk.core.drivers import Driver
from symulacja_mpk.utils.constants import TRACK_LEFT_BOUND, TRACK_RIGHT_LIMIT

bus_image = None
tram_image = None

def set_vehicle_images(bus_img: pygame.Surface, tram_img: pygame.Surface):
    global bus_image, tram_image
    bus_image = bus_img
    tram_image = tram_img

class Vehicle(ABC): # abstrakcyjna klasa bazowa dla każdego busa/tramwaju. Posiada własny numer linii, trasę, kierowcę, prędkość poruszania się
    def __init__(self, line_number: str, route: Route, driver: Driver, speed: float = 1.0):
        self.line_number = line_number
        self.route = route
        self.driver = driver
        self.base_speed = speed  # bazowa prędkość pojazdu
        self.speed = speed * self.driver.get_speed_multiplier()
        self.state = "Good"
        self.condition = 10  # 10 to najlepszy stan; nowy/naprawiony
        self.repair_duration = 0.0
        self.x = TRACK_LEFT_BOUND
        self.direction = 1
        self.y = 0
        self.hours_driven = 0.0
        self.time_broken = 0.0
        self.wait_timer = 0.0
        self.stop_positions = route.get_stop_positions()
        self.next_stop_index = 0
        self.active = False # czy jest na trasie
        self.activation_time = 0.0 # czas, zanim odjedzie a się pojawi na trasie
        self.breakdown_duration = 0.0
        self.cost_tracker = None

    @abstractmethod
    def calculate_cost(self) -> float: # abstrakcyjna metoda, która oblicza koszty operacyjne danego pojazdu
        pass

    @abstractmethod
    def get_image(self) -> pygame.Surface:
        pass

    def update(self, dt: float, delay_factor: float, current_time: float): # Aktualizacja stanu pojazdu w symulacji (ruch, obsługa awarii, postój na przystankach oraz aktywację pojazdu). Przyjmuje dt, czyli czas od aktualizacji w ms, delay_factor, czyli współczynnik opóźnienia i current_time, czyli obecny czas symulacji w sekundach
        if not self.active:
            if current_time >= self.activation_time:
                self.active = True
            else:
                return

        if self.state == "Broken":
            self.time_broken += dt / 1000.0

            if self.time_broken < self.breakdown_duration: # pojazd uszkodzony
                return

            if self.time_broken < self.breakdown_duration + self.repair_duration: # naprawa
                return

            self.state = "Good"
            self.time_broken = 0.0
            self.condition = 10
            return

        if self.wait_timer > 0:
            self.wait_timer -= dt / 1000.0
            return

        self.x += self.direction * (self.speed / delay_factor)

        if self.direction == 1 and self.x >= TRACK_RIGHT_LIMIT: # zmiana kierunku przy pętli
            self.direction = -1
            self.stop_positions = list(reversed(self.stop_positions))
            self.next_stop_index = 0
            self.x = TRACK_RIGHT_LIMIT
        elif self.direction == -1 and self.x <= TRACK_LEFT_BOUND:
            self.direction = 1
            self.stop_positions = list(reversed(self.stop_positions))
            self.next_stop_index = 0
            self.x = TRACK_LEFT_BOUND

        if self.next_stop_index < len(self.stop_positions): # obsługa przystanków
            stop_x = self.stop_positions[self.next_stop_index]
            if (self.direction == 1 and self.x >= stop_x) or (self.direction == -1 and self.x <= stop_x):
                self.x = stop_x # Upewnij się, że pojazd jest dokładnie na przystanku
                self.wait_timer = 5.0
                self.next_stop_index += 1
                if self.next_stop_index >= len(self.stop_positions):
                    self.next_stop_index = 0


class Bus(Vehicle): # klasa autobus, która porusza się po trasie
    def __init__(self, line_number: str, route: Route, driver: Driver, fuel_consumption: float, speed: float = 1.0): # Konstruktor, który tworzy obiekt autobus. Jako argumenty przyjmuje: nr linii, trasę, kierowcę, zużycie paliwa, prędkość.
        super().__init__(line_number, route, driver, speed) # konstruktor dziedziczy po klasie vehicle
        self.fuel_consumption = fuel_consumption

    def calculate_cost(self) -> float:
        return self.fuel_consumption * self.route.get_length() + self.driver.salary

    def get_image(self) -> pygame.Surface:
        return bus_image

class Tram(Vehicle): # klasa tramwaj, która porusza się po trasie
    def __init__(self, line_number: str, route: Route, driver: Driver, electricity_consumption: float, speed: float = 1.0): # Konstruktor, który tworzy obiekt tramwaj. Jako argumenty przyjmuje: nr linii, trasę, kierowcę, zużycie energii, prędkość.
        super().__init__(line_number, route, driver, speed)
        self.electricity_consumption = electricity_consumption

    def calculate_cost(self) -> float:
        return self.electricity_consumption * self.route.get_length() + self.driver.salary

    def get_image(self) -> pygame.Surface:
        return tram_image