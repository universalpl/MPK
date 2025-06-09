import sys
import random
from abc import ABC, abstractmethod
from typing import List
from enum import Enum
import os
import csv
import sys
import subprocess

try:
    import pygame
except ImportError:
    print("Instalowanie PyGame")

    command = [ # wybranie odpowiedniej komendy dla systemu
        sys.executable, "-m", "pip", "install", "pygame"
    ] if sys.platform != "win32" else [
        "py", "-m", "pip", "install", "pygame"
    ]

    subprocess.check_call(command) # wykonanie instalacji
    os.execv(sys.executable, [sys.executable] + sys.argv)

import pygame

pygame.init()


class TimePeriod(Enum):  # pory dnia - względem nich są opóźnienia/korki
    MORNING = 1
    MIDDAY = 2
    AFTERNOON = 3
    EVENING = 4


class Traffic:  # warunki ruchu drogowego
    def __init__(self, intensity: int, period: TimePeriod):
        self._intensity = intensity
        self._period = period

    def get_delay_factor(
            self) -> float:  # współczynnik opóźnienia; im większe niż 1.0, tym większe opóźnienie przez intensywność trasy
        return 1 + (self._intensity / 10)


class Route:  # ukazanie trasy pojazdu, listy przystanków, długości oraz warunków ruchu trasy
    def __init__(self, stops: List[str], length: float, traffic):
        self.__stops = stops
        self.__length = length
        self.__traffic = traffic

    def get_stops(self) -> List[str]:
        return self.__stops

    def get_length(self) -> float:
        return self.__length

    def get_traffic(self):
        return self.__traffic

    def get_delay_factor(
            self) -> float:  # współczynnik opóźnienia; im większe niż 1.0, tym większe opóźnienie przez warunki ruchu
        return self.__traffic.get_delay_factor()

    def get_stop_positions(self) -> List[int]:  # zwraca listę pozycji w poziomie dla każdego przystanku na trasie
        if len(self.__stops) <= 1:
            return [50 + (TRACK_RIGHT_LIMIT - 50) // 2]

        available_width = TRACK_RIGHT_LIMIT - 50
        return [50 + i * (available_width // (len(self.__stops) - 1)) for i in range(len(self.__stops))]


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


class CarefulDriver(Driver): # wolniejszy - mniejsze ryzyko
    def __init__(self, name: str, salary: float):
        super().__init__(name, salary)

    def get_speed_multiplier(self) -> float:
        return 0.8

    def get_failure_risk_multiplier(self) -> float:
        return 0.5


class AggressiveDriver(Driver): # szybszy - większe ryzyko
    def __init__(self, name: str, salary: float):
        super().__init__(name, salary)

    def get_speed_multiplier(self) -> float:
        return 1.2

    def get_failure_risk_multiplier(self) -> float:
        return 3


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
        self.x = 50
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

    @abstractmethod
    def calculate_cost(self) -> float: # abstrakcyjna metoda, która oblicza koszty operacyjne danego pojazdu
        pass

    def update(self, dt, delay_factor, current_time): # aktualizacja stanu pojazdu w symulacji (ruch, obsługa awarii, postój na przystankach oraz aktywację pojazdu). Przyjmuje dt, czyli czas od aktualizacji w ms, delay_factor, czyli współczynnik opóźnienia i current_time, czyli obecny czas symulacji w sekundach
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
            self.x = TRACK_RIGHT_LIMIT  # "przypnij" na koniec
        elif self.direction == -1 and self.x <= TRACK_LEFT_BOUND:
            self.direction = 1
            self.stop_positions = list(reversed(self.stop_positions))
            self.next_stop_index = 0
            self.x = TRACK_LEFT_BOUND  # przypnij na początek

        if self.next_stop_index < len(self.stop_positions): # osbługiwanie przystanków
            stop_x = self.stop_positions[self.next_stop_index]
            if abs(self.x - stop_x) < 2:
                self.wait_timer = 5.0
                self.next_stop_index += 1
                if self.next_stop_index >= len(self.stop_positions):
                    self.next_stop_index = 0


class Bus(Vehicle): # klasa autobus, która porusza się po trasie
    def __init__(self, line_number: str, route: Route, driver: Driver, fuel_consumption: float, speed: float = 1.0): # konstruktor, który tworzy obiekt autobus. Jako argumenty przyjmuje: nr linii, trasę, kierowcę, zużycie paliwa, prędkość.
        super().__init__(line_number, route, driver, speed) # konstruktor dziedzicy po rodzicu, czyli klasie vehicle
        self.fuel_consumption = fuel_consumption

    def calculate_cost(self) -> float:
        return self.fuel_consumption * self.route.get_length() + self.driver.salary

    def get_image(self):
        return bus_image

class Tram(Vehicle): # klasa tramwaj, która porusza się po trasie
    def __init__(self, line_number: str, route: Route, driver: Driver, electricity_consumption: float, speed: float = 1.0): # konstruktor, który tworzy obiekt tramwaj. Jako argumenty przyjmuje: nr linii, trasę, kierowcę, zużycie energii, prędkość.
        super().__init__(line_number, route, driver, speed) # konstruktor dziedzicy po rodzicu, czyli klasie vehicle
        self.electricity_consumption = electricity_consumption

    def calculate_cost(self) -> float:
        return self.electricity_consumption * self.route.get_length() + self.driver.salary

    def get_image(self):
        return tram_image


class Maintenance: # klasa odpowiedzialna za symulację awarii pojazdów i kondycji
    def __init__(self, base_failure_chance_per_second: float = 0.01): # konstruktor, base_failrue..., czyli podstawowa szansa na awarię
        self.base_failure_chance = base_failure_chance_per_second

    def check_failure(self, vehicle: Vehicle, dt: float): # metoda sprawdza, czy pojazd uległ awarii i aktualizuję stan. Im niższa kondycja, tym większa szansa na awarię. Argumenty to vehicle, czyli pojazd do sprawdzenia oraz dt, czyli czas, jaki upłynął od ostatniej aktualizacji w ms
        if vehicle.condition > 0:
            vehicle.hours_driven += dt / 1000.0 / 60.0 / 60.0
            risk_multiplier = 11 - vehicle.condition
            failure_chance = self.base_failure_chance * risk_multiplier
            if random.random() < failure_chance * (dt / 1000.0):
                vehicle.condition -= 1
                if vehicle.condition <= 0:
                    vehicle.state = "Broken"
                    vehicle.time_broken = 0.0
                    vehicle.breakdown_duration = random.randint(5, 30)
                    vehicle.repair_duration = random.uniform(5.0, 15.0)
                    if hasattr(vehicle, "cost_tracker"): # dodanie kosztów do "trakcera" kosztów
                        vehicle.cost_tracker.add_repair_cost(vehicle.repair_duration)

        elif vehicle.state == "Broken":
            vehicle.time_broken += dt / 1000.0


#koszty
class CostTracker: # klasa, która śledzi i oblicza koszty operacyjne dla pojazdu
    def __init__(self, vehicle_id, driver_salary_per_hour, consumption_per_km, is_tram=False): # inicjalizacja obiektu CostTracker. Jako argumenty przyjmuje: vehicle_id, czyli identyfikator danego pojazdu, driver_salary..., czyli stawka za godzinę dla kierowcy, consumption..., zużycie paliwa/prądu na km, is_tram, czyli stwierdzenie jaki to pojazd
        self.vehicle_id = vehicle_id
        self.salary = 0.0
        self.fuel = 0.0
        self.total_cost = 0.0
        self.driver_salary_per_hour = driver_salary_per_hour
        self.consumption_per_km = consumption_per_km
        self.is_tram = is_tram
        self.last_x = 50
        self.elapsed_time = 0 # całkowity czas
        self.repair_cost = 0.0 # całkowity koszt napraw

    def update(self, v: Vehicle, dt: float): # metoda, która aktualizuje koszty pojazdu; oblicza pensję i zużycia. Argumenty przyjmowane: v - obiekt pojazdu do aktualizacji kosztów, dt - analogicznie jak wyżej opisane
        seconds = dt / 1000.0
        self.salary += (self.driver_salary_per_hour / 3600.0) * seconds

        distance_moved = abs(v.x - self.last_x) / 100.0
        self.fuel += self.consumption_per_km * distance_moved
        self.last_x = v.x

        self.total_cost = self.salary + self.fuel

    def to_dict(self, time_seconds): # formatuje dane kosztów do słownika, by zapisać do pliku CSV. Arg.: time_sec - aktualny czas symulacji w s. Zwraca słownik, który zawiera obecne kosty danego pojazdu
        return {
            'czas_s': int(time_seconds),
            'pojazd': self.vehicle_id,
            'typ': 'Tram' if self.is_tram else 'Bus',
            'paliwo_energia': round(self.fuel, 2),
            'pensja': round(self.salary, 2),
            'naprawy': round(self.repair_cost, 2),
            'suma': round(self.salary + self.fuel + self.repair_cost, 2)
        }

    def add_repair_cost(self, seconds): # metoda kosztu naprawy do wszystkich kosztów i jako argument przyjmuje czas trwania awarii w s
        self.repair_cost += seconds * 1.0  # 1 zł kosztu naprawy za sekundę zepsucia


pygame.init()
screen = pygame.display.set_mode((1000, 600))

try: # obsługa błędów w ładowaniu obrazów i samo ładowanie
    bus_image = pygame.image.load('bus_r.png').convert_alpha()
    tram_image = pygame.image.load('tram_r.png').convert_alpha()
    bus_image = pygame.transform.scale(bus_image, (60, 30))
    tram_image = pygame.transform.scale(tram_image, (60, 30))
except pygame.error as e:
    print(f"Error loading image: {e}. Make sure bus_r.png and tram_r.png are in the program directory.")
    bus_image = pygame.Surface((60, 30), pygame.SRCALPHA)
    bus_image.fill((0, 0, 255, 128)) # trochę niebieski prostokąt zastępujący autobus
    tram_image = pygame.Surface((60, 30), pygame.SRCALPHA)
    tram_image.fill((255, 0, 0, 128)) # trochę czerwony prostokąt zastępujący tramwaj

pygame.display.set_caption("Symulacja MPK Wrocław") # tytuł
clock = pygame.time.Clock()

BLUE = (0, 102, 204) #kolory
YELLOW = (255, 215, 0)
RED = (255, 0, 0)
GRAY = (200, 200, 200)
BLACK = (0, 0, 0)
GREEN = (144, 238, 144)
PANEL_BG = (240, 240, 240)

font = pygame.font.SysFont(None, 20)

PANEL_WIDTH = 140 # ustawianie granic panelu oraz dróg
PANEL_LEFT_X = 1000 - PANEL_WIDTH
TRACK_LEFT_BOUND = 50
TRACK_RIGHT_BOUND = PANEL_LEFT_X - 10
TRACK_RIGHT_LIMIT = TRACK_RIGHT_BOUND  # do poruszania się i zatzymywania


routes = [ # nazwy przystanków, poszczególne trasy oraz warunki - długość i natężenie z porą dnia
    Route(["Dworzec Główny", "Rynek", "Opera", "Narodowe Forum Muzyki"], 12, Traffic(4, TimePeriod.MORNING)),
    Route(["Park Południowy", "Aquapark", "Dworzec Autobusowy", "Plac Świebodzki"], 10, Traffic(3, TimePeriod.MIDDAY)),
    Route(["Swojczyce", "Pasaż Grunwaldzki", "Zoo", "Krzyki"], 11, Traffic(5, TimePeriod.AFTERNOON)),
    Route(["Metalowców", "Stadion Olimpijski", "Na Ostatnim Groszu", "Grabiszyński Park"], 13,
          Traffic(6, TimePeriod.EVENING)),
]

def create_random_drivers_pool(num_drivers: int) -> List[Driver]: # tworzy pule kierowców z losowym wynagrodzeniem i stylem jazdy
    drivers = []
    driver_types = [CarefulDriver, NormalDriver, AggressiveDriver]
    base_salary = 3000

    for i in range(num_drivers):
        chosen_driver_class = random.choice(driver_types)
        salary = base_salary + i * 50

        driver_name = f"{chosen_driver_class.__name__.replace('Driver', '')} {i + 1}"

        driver = chosen_driver_class(driver_name, salary)
        drivers.append(driver)

    random.shuffle(drivers)
    return drivers

total_vehicles = len(routes) * 3 # ilość pojazdów
drivers_pool = create_random_drivers_pool(total_vehicles)

vehicles = []
maintenance = Maintenance()
y_base = [100, 200, 300, 400] # domyślne pozycje pionowe dla trasy danej

for line_index, route in enumerate(routes): # tworzenie pojazdów i właściwości
    for i in range(3):

        if drivers_pool:
            driver = drivers_pool.pop(0)  # pierwszy kierowaca z puli
        else:
            driver = NormalDriver(f"Default Driver {line_index * 3 + i}", 3000) # jeżeli brak kierowców w puli to deafult

        if line_index < 2: # autobusy mają 2 pierwsze trasy
            vehicle = Bus(
                line_number=f"B{line_index * 3 + i + 1}",
                route=route,
                driver=driver,
                fuel_consumption=0.3 + i * 0.05,
                speed=0.7 + i * 0.05
            )
            vehicle.cost_tracker = CostTracker(vehicle.line_number, driver.salary, 0.3 + i * 0.05, is_tram=False)
        else:
            vehicle = Tram(
                line_number=f"T{(line_index - 2) * 3 + i + 1}",
                route=route,
                driver=driver,
                electricity_consumption=0.4 + i * 0.03,
                speed=0.8 + i * 0.05
            )
            vehicle.cost_tracker = CostTracker(vehicle.line_number, driver.salary, 0.4 + i * 0.03, is_tram=True)

        vehicle.y = y_base[line_index]  # domyślny Y dla pojazdu
        vehicle.activation_time = i * 15  # aktywacja po starcie symulacji kolejnych pojazdów na linii
        vehicles.append(vehicle)


def draw_routes(): # metoda do rysowania tras i przystanków z nazwami
    for idx, route in enumerate(routes):
        base_y = y_base[idx]
        pygame.draw.line(screen, GRAY, (TRACK_LEFT_BOUND, base_y), (TRACK_RIGHT_BOUND, base_y), 3)

        for i, x_stop in enumerate(route.get_stop_positions()):
            effective_x_stop = min(x_stop, TRACK_RIGHT_BOUND)
            pygame.draw.circle(screen, BLACK, (int(effective_x_stop), base_y), 5)

            stop_name = route.get_stops()[i]
            label = font.render(stop_name, True, BLACK)
            label_rect = label.get_rect()
            text_x = effective_x_stop - label_rect.width // 2
            text_x = max(TRACK_LEFT_BOUND, min(text_x, TRACK_RIGHT_BOUND - label_rect.width)) # zapobieganie wyjściu nazw przystanków poza granice toru
            screen.blit(label, (text_x, base_y + 10))


def draw_vehicle(v: Vehicle): # rysuje pojazdy, patrzy na typ, kierunek oraz stan
    if not v.active:
        return
    image = v.get_image()
    draw_x = min(v.x, TRACK_RIGHT_LIMIT - image.get_width() / 2)
    draw_x = max(draw_x, TRACK_LEFT_BOUND)
    if v.direction == -1: # odwracanie pojazdu
        image = pygame.transform.flip(image, True, False)
    screen.blit(image, (draw_x, v.y - image.get_height() / 2))
    if v.state == "Broken":
        pygame.draw.rect(screen, RED, (draw_x, v.y - image.get_height() / 2, image.get_width(), image.get_height()), 2)


def draw_info_panel(vehicles): # panel informacyjny po prawej stronie. Wyświetla statusy pojazdów i obsługuje przewijanie. Jako argument przyjmuje vehicles... - lista obiektów pojazdów do wyświetlania
    global scroll_offset
    panel_left = 1000 - PANEL_WIDTH
    pygame.draw.rect(screen, PANEL_BG, (panel_left, 0, PANEL_WIDTH, 600))

    content_height = 0
    for v in vehicles:
        if v.active:
            content_height += (4 * 18) + 10

    panel_display_height = 600
    max_scroll_offset = max(0, content_height - panel_display_height + 20)

    scroll_offset = max(0, min(scroll_offset, max_scroll_offset))

    y = 10 - scroll_offset
    for v in vehicles:
        if not v.active:
            continue
        lines = [
            f"Line: {v.line_number}",
            f"Type: {'Bus' if isinstance(v, Bus) else 'Tram'}",
            f"Driver: {v.driver.name}",
            f"Status: {v.condition if v.state == 'Good' else 'Breakdown'}" # zamiast good skala 1-10
        ]
        for line in lines:
            label = font.render(line, True, BLACK)
            screen.blit(label, (panel_left + 10, y))
            y += 18
        y += 10

scroll_offset = 0

running = True # pętla całej gry
start_time = pygame.time.get_ticks() / 1000.0

while running:
    dt = clock.tick(60)
    current_time = pygame.time.get_ticks() / 1000.0 - start_time

    for event in pygame.event.get():
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 4:  # scroll w górę
                scroll_offset = max(scroll_offset - 20, 0)
            elif event.button == 5:  # scroll w dół
                scroll_offset += 20
        if event.type == pygame.QUIT:
            running = False

    screen.fill(GREEN)
    draw_routes()

    for v in vehicles:
        maintenance.check_failure(v, dt)
        v.update(dt, v.route.get_delay_factor(), current_time)
        if v.active:
            v.cost_tracker.update(v, dt)
        draw_vehicle(v)

    if int(current_time) % 10 == 0 and int(current_time) != int(current_time - dt / 1000.0): # zapisywanie kosztów do csv
        file_exists = os.path.isfile("koszty.csv")
        with open("koszty.csv", "a", newline='', encoding='utf-8') as csvfile:  # Added encoding
            fieldnames = ['czas_s', 'pojazd', 'typ', 'paliwo_energia', 'pensja', 'naprawy', 'suma']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            for v in vehicles:
                if v.active:
                    writer.writerow(v.cost_tracker.to_dict(current_time))

    draw_info_panel(vehicles)

    pygame.display.flip()

pygame.quit()
sys.exit()