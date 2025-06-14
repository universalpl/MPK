from symulacja_mpk.core.vehicles import Vehicle

class CostTracker: # klasa, która śledzi i oblicza koszty operacyjne dla pojazdu
    def __init__(self, vehicle_id: str, driver_salary_per_hour: float, consumption_per_km: float, is_tram: bool = False): # inicjalizacja obiektu CostTracker. Jako argumenty przyjmuje: vehicle_id, czyli identyfikator danego pojazdu, driver_salary..., czyli stawka za godzinę dla kierowcy, consumption..., zużycie paliwa/prądu na km, is_tram, czyli stwierdzenie, jaki to pojazd
        self.vehicle_id = vehicle_id
        self.salary = 0.0
        self.fuel_electricity_cost = 0.0 # Zmiana nazwy, aby objąć paliwo/energię
        self.driver_salary_per_hour = driver_salary_per_hour
        self.consumption_per_km = consumption_per_km
        self.is_tram = is_tram
        self.last_x = 50 # Startowa pozycja pojazdu
        self.repair_cost = 0.0 # całkowity koszt napraw

    def update(self, v: Vehicle, dt: float): # metoda, która aktualizuje koszty pojazdu; oblicza pensję i zużycia. Argumenty przyjmowane: v - obiekt pojazdu do aktualizacji kosztów, dt - analogicznie jak wyżej opisane
        seconds = dt / 1000.0
        self.salary += (self.driver_salary_per_hour / 3600.0) * seconds

        distance_moved = abs(v.x - self.last_x) / 1000.0 # Przeliczanie na km - /1000.0, zakładając że 1 jednostka na osi X to 1 metr
        self.fuel_electricity_cost += self.consumption_per_km * distance_moved
        self.last_x = v.x

    def to_dict(self, time_seconds: float) -> dict: # formatuje dane kosztów do słownika, by zapisać do pliku CSV. Arg.: time_sec - aktualny czas symulacji w s. Zwraca słownik, który zawiera obecne kosty danego pojazdu
        return {
            'czas_s': int(time_seconds),
            'pojazd': self.vehicle_id,
            'typ': 'Tram' if self.is_tram else 'Bus',
            'paliwo_energia': round(self.fuel_electricity_cost, 2),
            'pensja': round(self.salary, 2),
            'naprawy': round(self.repair_cost, 2),
            'suma': round(self.salary + self.fuel_electricity_cost + self.repair_cost, 2)
        }

    def add_repair_cost(self, seconds: float): # metoda kosztu naprawy do wszystkich kosztów i jako argument przyjmuje czas trwania awarii w s
        self.repair_cost += seconds * 1.0  # 1 zł kosztu naprawy za sekundę zepsucia