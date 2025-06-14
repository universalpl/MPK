import pygame
import sys
import random
import os
import csv
from typing import List

from symulacja_mpk.core.traffic import Traffic, TimePeriod
from symulacja_mpk.core.route import Route
from symulacja_mpk.core.drivers import NormalDriver, CarefulDriver, AggressiveDriver, Driver
from symulacja_mpk.core.vehicles import Bus, Tram, set_vehicle_images # Importuj funkcję do ustawiania obrazków
from symulacja_mpk.core.maintenance import Maintenance
from symulacja_mpk.utils.cost_tracker import CostTracker
from symulacja_mpk.utils.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, GREEN,
    BUS_IMAGE_PATH, TRAM_IMAGE_PATH, VEHICLE_IMAGE_WIDTH, VEHICLE_IMAGE_HEIGHT
)
from symulacja_mpk.gui.display import draw_routes, draw_vehicle, draw_info_panel, handle_scroll

pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

bus_image_loaded = None
tram_image_loaded = None
try:
    bus_image_loaded = pygame.image.load(os.path.join(os.path.dirname(__file__), '..', BUS_IMAGE_PATH)).convert_alpha() # os.path.join(os.path.dirname(__file__), '..', BUS_IMAGE_PATH) tworzy ścieżkę do obrazka.
    tram_image_loaded = pygame.image.load(os.path.join(os.path.dirname(__file__), '..', TRAM_IMAGE_PATH)).convert_alpha() # '..' cofa się o jeden katalog w górę (z symulacja_mpk do MPK)
    bus_image_loaded = pygame.transform.scale(bus_image_loaded, (VEHICLE_IMAGE_WIDTH, VEHICLE_IMAGE_HEIGHT))
    tram_image_loaded = pygame.transform.scale(tram_image_loaded, (VEHICLE_IMAGE_WIDTH, VEHICLE_IMAGE_HEIGHT))
except pygame.error as e:
    print(f"Błąd ładowania obrazu: {e}. Upewnij się, że {BUS_IMAGE_PATH} i {TRAM_IMAGE_PATH} są w katalogu")
    bus_image_loaded = pygame.Surface((VEHICLE_IMAGE_WIDTH, VEHICLE_IMAGE_HEIGHT), pygame.SRCALPHA)
    bus_image_loaded.fill((0, 0, 255, 128)) # trochę niebieski prostokąt zastępujący autobus
    tram_image_loaded = pygame.Surface((VEHICLE_IMAGE_WIDTH, VEHICLE_IMAGE_HEIGHT), pygame.SRCALPHA)
    tram_image_loaded.fill((255, 0, 0, 128)) # trochę czerwony prostokąt zastępujący tramwaj

# Ustaw obrazy w module vehicles
set_vehicle_images(bus_image_loaded, tram_image_loaded)

pygame.display.set_caption("Symulacja MPK Wrocław") # tytuł
clock = pygame.time.Clock()

routes = [ # nazwy przystanków, poszczególne trasy oraz warunki - długość i natężenie z porą dnia
    Route(["Dworzec Główny", "Rynek", "Opera", "Narodowe Forum Muzyki"], 12, Traffic(4, TimePeriod.MORNING)),
    Route(["Park Południowy", "Aquapark", "Dworzec Autobusowy", "Plac Świebodzki"], 10, Traffic(3, TimePeriod.MIDDAY)),
    Route(["Swojczyce", "Pasaż Grunwaldzki", "Zoo", "Krzyki"], 11, Traffic(5, TimePeriod.AFTERNOON)),
    Route(["Metalowców", "Stadion Olimpijski", "Na Ostatnim Groszu", "Grabiszyński Park"], 13, Traffic(6, TimePeriod.EVENING)),
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

running = True # pętla całej gry
start_time = pygame.time.get_ticks() / 1000.0
last_csv_write_time = 0 # Śledzenie czasu ostatniego zapisu do CSV

while running:
    dt = clock.tick(60)
    current_time = pygame.time.get_ticks() / 1000.0 - start_time

    for event in pygame.event.get():
        if event.type == pygame.MOUSEBUTTONDOWN:
            handle_scroll(event)
        if event.type == pygame.QUIT:
            running = False

    screen.fill(GREEN)
    draw_routes(screen, routes, y_base)

    for v in vehicles:
        maintenance.check_failure(v, dt)
        v.update(dt, v.route.get_delay_factor(), current_time)
        if v.active and v.cost_tracker:
            v.cost_tracker.update(v, dt)
        draw_vehicle(screen, v)

    # Zapisywanie kosztów do csv co 10 sekund. current_time // 10 * 10 zaokrągla czas w dół do najbliższej dziesiątki
    rounded_current_time = int(current_time // 10 * 10)
    if rounded_current_time > last_csv_write_time:
        file_exists = os.path.isfile(os.path.join(os.path.dirname(__file__), '..', "koszty.csv")) # Ścieżka do koszty.csv
        with open(os.path.join(os.path.dirname(__file__), '..', "koszty.csv"), "a", newline='', encoding='utf-8') as csvfile:
            fieldnames = ['czas_s', 'pojazd', 'typ', 'paliwo_energia', 'pensja', 'naprawy', 'suma']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            for v in vehicles:
                if v.active and v.cost_tracker:
                    writer.writerow(v.cost_tracker.to_dict(current_time))
        last_csv_write_time = rounded_current_time


    draw_info_panel(screen, vehicles)

    pygame.display.flip()

pygame.quit()
sys.exit()