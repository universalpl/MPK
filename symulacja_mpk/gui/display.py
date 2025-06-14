import pygame
from typing import List
from symulacja_mpk.core.vehicles import Vehicle, Bus, Tram
from symulacja_mpk.core.route import Route
from symulacja_mpk.utils.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, PANEL_WIDTH, PANEL_LEFT_X,
    TRACK_LEFT_BOUND, TRACK_RIGHT_BOUND, TRACK_RIGHT_LIMIT,
    BLACK, GRAY, RED, PANEL_BG, FONT_NAME, FONT_SIZE
)

pygame.font.init()
font = pygame.font.SysFont(FONT_NAME, FONT_SIZE)

scroll_offset = 0

def draw_routes(screen: pygame.Surface, routes: List[Route], y_base: List[int]): # metoda do rysowania tras i przystanków z nazwami
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


def draw_vehicle(screen: pygame.Surface, v: Vehicle): # rysuje pojazdy, patrzy na typ, kierunek oraz stan
    if not v.active:
        return
    image = v.get_image()
    draw_x = v.x - image.get_width() / 2
    draw_x = max(TRACK_LEFT_BOUND, min(draw_x, TRACK_RIGHT_LIMIT - image.get_width()))
    if v.direction == -1: # odwracanie pojazdu
        image = pygame.transform.flip(image, True, False)
    screen.blit(image, (draw_x, v.y - image.get_height() / 2))
    if v.state == "Broken":
        pygame.draw.rect(screen, RED, (draw_x, v.y - image.get_height() / 2, image.get_width(), image.get_height()), 2)


def draw_info_panel(screen: pygame.Surface, vehicles: List[Vehicle]): # Panel informacyjny po prawej stronie. Wyświetla statusy pojazdów i obsługuje przewijanie. Jako argument przyjmuje vehicles... - lista obiektów pojazdów do wyświetlania
    global scroll_offset
    panel_left = PANEL_LEFT_X
    pygame.draw.rect(screen, PANEL_BG, (panel_left, 0, PANEL_WIDTH, SCREEN_HEIGHT))

    content_height = 0
    active_vehicles_count = sum(1 for v in vehicles if v.active)
    content_height = active_vehicles_count * ((4 * 18) + 10)

    panel_display_height = SCREEN_HEIGHT
    max_scroll_offset = max(0, content_height - panel_display_height + 20)

    scroll_offset = max(0, min(scroll_offset, max_scroll_offset)) # Ograniczanie scroll_offset

    y = 10 - scroll_offset
    for v in vehicles:
        if not v.active:
            continue
        lines = [
            f"Line: {v.line_number}",
            f"Type: {'Bus' if isinstance(v, Bus) else 'Tram'}",
            f"Driver: {v.driver.name}",
            f"Status: {v.condition if v.state == 'Good' else 'Broken'}" # zamiast good skala 1-10
        ]
        for line in lines:
            label = font.render(line, True, BLACK)
            screen.blit(label, (panel_left + 10, y))
            y += 18
        y += 10

def handle_scroll(event: pygame.event.Event):
    global scroll_offset
    if event.button == 4:  # scroll w górę
        scroll_offset = max(scroll_offset - 20, 0)
    elif event.button == 5:  # scroll w dół
        scroll_offset += 20