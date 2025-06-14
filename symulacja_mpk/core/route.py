from typing import List
from symulacja_mpk.core.traffic import Traffic
from symulacja_mpk.utils.constants import TRACK_LEFT_BOUND, TRACK_RIGHT_LIMIT

class Route:  # ukazanie trasy pojazdu, listy przystanków, długości oraz warunków ruchu trasy
    def __init__(self, stops: List[str], length: float, traffic: Traffic):
        self.__stops = stops
        self.__length = length
        self.__traffic = traffic

    def get_stops(self) -> List[str]:
        return self.__stops

    def get_length(self) -> float:
        return self.__length

    def get_traffic(self) -> Traffic:
        return self.__traffic

    def get_delay_factor(self) -> float:  # współczynnik opóźnienia; im większe niż 1.0, tym większe opóźnienie przez warunki ruchu
        return self.__traffic.get_delay_factor()

    def get_stop_positions(self) -> List[int]:  # zwraca listę pozycji w poziomie dla każdego przystanku na trasie
        if len(self.__stops) <= 1:
            return [TRACK_LEFT_BOUND + (TRACK_RIGHT_LIMIT - TRACK_LEFT_BOUND) // 2]

        available_width = TRACK_RIGHT_LIMIT - TRACK_LEFT_BOUND
        return [TRACK_LEFT_BOUND + i * (available_width // (len(self.__stops) - 1)) for i in range(len(self.__stops))]