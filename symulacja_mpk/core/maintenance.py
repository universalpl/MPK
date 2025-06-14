import random
from symulacja_mpk.core.vehicles import Vehicle

class Maintenance: # odpowiedzialna za awarie i kondycje pojazdów
    def __init__(self, base_failure_chance_per_second: float = 0.01): # konstruktor, base_failrue..., czyli podstawowa szansa na awarię
        self.base_failure_chance = base_failure_chance_per_second

    def check_failure(self, vehicle: Vehicle, dt: float): # Metoda sprawdza, czy pojazd uległ awarii i aktualizuję stan. Im niższa kondycja, tym większa szansa na awarię. Argumenty to vehicle, czyli pojazd do sprawdzenia oraz dt, czyli czas, jaki upłynął od ostatniej aktualizacji w ms
        if vehicle.condition > 0:
            vehicle.hours_driven += dt / 1000.0 / 60.0 / 60.0
            risk_multiplier = (11 - vehicle.condition) * vehicle.driver.get_failure_risk_multiplier()
            failure_chance = self.base_failure_chance * risk_multiplier
            if random.random() < failure_chance * (dt / 1000.0):
                vehicle.condition -= 1
                if vehicle.condition <= 0:
                    vehicle.state = "Broken"
                    vehicle.time_broken = 0.0
                    vehicle.breakdown_duration = random.randint(5, 30) # Czas samej awarii
                    vehicle.repair_duration = random.uniform(5.0, 15.0) # Czas, w którym pojazd jest naprawiany po awarii
                    if vehicle.cost_tracker: # dodanie kosztów do "trackera" kosztów
                        vehicle.cost_tracker.add_repair_cost(vehicle.repair_duration)

        elif vehicle.state == "Broken":
            pass