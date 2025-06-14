import pygame
import os

# Kolory
BLUE = (0, 102, 204)
YELLOW = (255, 215, 0)
RED = (255, 0, 0)
GRAY = (200, 200, 200)
BLACK = (0, 0, 0)
GREEN = (144, 238, 144)
PANEL_BG = (240, 240, 240)

# Ustawienia ekranu i panelu
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 600
PANEL_WIDTH = 140
PANEL_LEFT_X = SCREEN_WIDTH - PANEL_WIDTH

# Granice tras
TRACK_LEFT_BOUND = 50
TRACK_RIGHT_BOUND = PANEL_LEFT_X - 10
TRACK_RIGHT_LIMIT = TRACK_RIGHT_BOUND

FONT_SIZE = 20
FONT_NAME = None # Domyślna czcionka systemowa

BUS_IMAGE_PATH = 'bus_r.png'
TRAM_IMAGE_PATH = 'tram_r.png'

# Rozmiary obrazków pojazdów
VEHICLE_IMAGE_WIDTH = 60
VEHICLE_IMAGE_HEIGHT = 30