# ==========================================================================
# Python Snake
# ==========================================================================
# Python. Programación Estructurada
# FPP-PE-P12. SNAKE! 🐍
#   Centro: CIFP Carlos III
#   Autor: Pablo García Collado
#   Fecha: Enero 2026
# --------------------------------------------------------------------------
# (C) 2026 Paul G. Collado
# --------------------------------------------------------------------------
# Version
# 1.1.0 - Adaptado a POO (Clases)
# 1.0.0 - Programa completado
# --------------------------------------------------------------------------

# ==========================================================================
# IMPORTACIÓN DE LAS LIBRERIAS
# 
# Estas son las librerías necesarias para que el programa funcione.
import sys, tty, termios
import threading
import time
import random
import pickle
import os

from abc import ABC, abstractmethod

# ==========================================================================
# VARIABLES GLOBALES
#
# Estas son las variables que serán accesibles desde cualquier parte del programa
# --------------------------------------------------------------------------
global key_pressed

lines = 15
columns = 50
initial_position = [(10, 10), (10, 9), (10, 8), (10, 7)]
key_pressed = "R"

# ==========================================================================
# CLASES
#
class Drawable(ABC):
    """Clase abstracta Drawable"""
    @abstractmethod
    def draw(self):
        pass

class Cursor:
    HIDE="\033[?25l"                                # HIDE CURSOR
    SHOW="\033[?25h"                                # SHOW CURSOR
    CLEAR_SCREEN="\033c"                            # CLEAR SCREEN
    S_R="\033[0m"                                   # STYLE RESET
    S_D="\033[2m"                                   # STYLE DIM
    S_B="\033[1m"                                   # STYLE BOLD
    R_L="\033[2K"                                   # REMOVE LINE
    M_U="\033[A"                                    # MOVE UP 1 LINE

    @staticmethod
    def move_cursor(line: int, column: int) -> None:
        print(f"\033[{line};{column}H", end="")
    
    @staticmethod
    def move_and_print(position: tuple, text: str) -> None:
        Cursor.move_cursor(*position)
        print(text)

class Color:
    GREEN = "\033[32m"
    LIGHT_GREEN = "\033[92m"
    RED = "\033[31m"
    YELLOW = "\033[33m"
    LIGHT_RED = "\033[91m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    GRAY = "\033[37m"

class Map(Drawable):
    def __init__(self, lines, columns):
        self.lines = lines
        self.columns = columns
        self.banner = f"""  ╔═╗╦ ╦╔╦╗╦ ╦╔═╗╔╗╔  ╔═╗╔╗╔╔═╗╦╔═╔═╗
  ╠═╝╚╦╝ ║ ╠═╣║ ║║║║  ╚═╗║║║╠═╣╠╩╗╠╣ 
  ╩   ╩  ╩ ╩ ╩╚═╝╝╚╝  ╚═╝╝╚╝╩ ╩╩ ╩╚═╝     {Color.GRAY}DAW 2026"""
        
    @property
    def limits(self) -> dict:
        return { "U": 4, "D": self.lines + 5, "L": 1, "R": self.columns + 2 }
    
    def get_valid_range(self, snake) -> list:
        lines = list(range(self.limits['U'] + 1, self.limits['D']))
        columns = list(range(self.limits['L'] + 1, self.limits['R']))
        
        map_range = []
        for line in lines:
            for column in columns:
                coordenada = tuple([line, column])
                if coordenada not in snake.body:
                    map_range.append(coordenada)

        return map_range
    
    def draw(self) -> None:
        print(Cursor.CLEAR_SCREEN, end="")
        print(self.banner)

        print(f"▄" * (self.columns + 2))
        print(f"█{' ' * (self.columns)}█\n" * self.lines, end="")
        print(f"▀" * (self.columns + 2))

class Snake(Drawable):
    symbol = { "VERTICAL": f"█{Cursor.S_R}", "HORIZONTAL": f"■{Cursor.S_R}", "TURN": f"▮{Cursor.S_R}" }
    EAT_WAIT_TIME = 0.15

    def __init__(self, body):
        self.body = body
        self._direction = "R"
    
    @property
    def head(self):
        return self.body[0]
    
    @property
    def length(self):
        return len(self.body)
    
    @property
    def direction(self):
        return self._direction
    
    @direction.setter
    def direction(self, value):
        self._direction = value
    
    def move(self, last_direction) -> tuple:
        # CALCULAR NUEVA POSICIÓN
        movement = { "U": (-1, 0), "D": (1, 0), "L": (0, -1), "R": (0, 1) }
        newHead = self.head[0] + movement[self.direction][0], self.head[1] + movement[self.direction][1]
        self.body.insert(0, newHead)

        # PINTAR NUEVA CABEZA.
        character = self.symbol["HORIZONTAL"] if self.direction in ['L', 'R'] else self.symbol["VERTICAL"]
        Cursor.move_and_print(self.head, f"{Color.GREEN}{character}")

        # COMPROBAR SI HA GIRADO.
        if self.is_turning(last_direction):
            Cursor.move_and_print(self.body[1], f"{Color.GREEN}{self.symbol['TURN']}")

        # BORRAR LA COLA.
        tail = self.body.pop()
        Cursor.move_and_print(tail, " ")
        return tail
    
    def check_collision(self, map) -> bool:
        if self.head in self.body[1:] or not self.in_limits(map):
            return True
        return False
    
    def check_eat(self, tail, fruit) -> bool:
        if self.head == fruit.position:
            self.body.append(tail)
            Cursor.move_and_print(tail, f"{Color.GREEN}■{Cursor.S_R}")
            return True
        return False
    
    def is_invalid_move(self, new_direction, last_direction) -> str:
        opposites = { 'U': 'D', 'D': 'U', 'L': 'R', 'R': 'L' }
        return new_direction == opposites[last_direction]

    def in_limits(self, map) -> bool:
        if not map.limits['D'] > self.head[0] > map.limits['U']:
            return False
        elif not map.limits['L'] < self.head[1] < map.limits['R']:
            return False
        return True
    
    def is_turning(self, last_direction) -> bool:
        vertical = ['U', 'D']
        horizontal = ['L', 'R']

        if self.direction in vertical and last_direction in horizontal:
            return True
        elif self.direction in horizontal and last_direction in vertical:
            return True
        return False
    
    def change_head_color(self, color, reset_color) -> None:
        character = self.symbol["HORIZONTAL"] if self.direction in ['L', 'R'] else self.symbol["VERTICAL"]
        Cursor.move_and_print(self.head, f"{color}{character}{Cursor.S_R}")
        if reset_color:
            time.sleep(self.EAT_WAIT_TIME)
            Cursor.move_and_print(self.head, f"{Color.GREEN}{character}{Cursor.S_R}")
    
    def draw(self) -> None:
        for fila, columna in self.body:
            Cursor.move_and_print([fila, columna], f"{Color.GREEN}{self.symbol['HORIZONTAL']}")

class Fruit(Drawable):
    symbol = f"⬤{Cursor.S_R}"

    def __init__(self, range):
        self.position = (random.choice(range))
        self.color = self._get_random_color()
    
    def _get_random_color(self) -> str:
        colors = [Color.GREEN, Color.LIGHT_GREEN, Color.RED, Color.YELLOW, Color.LIGHT_RED, Color.BLUE, Color.MAGENTA, Color.CYAN, Color.GRAY]
        return random.choice(colors)
    
    def draw(self) -> tuple:
        Cursor.move_and_print(self.position, f"{self.color}{self.symbol}")
    
class ScoreManager(Drawable):
    SCORE_MAX_LENGTH = 10
    path = "./scores.pkl"
    scores = []

    def save(self, username, score) -> tuple:
        registro = tuple((time.time(), username, score))
        self.scores.append(registro)
        with open(self.path, 'wb') as file:
            pickle.dump(self.scores, file)
            return registro

    def load(self) -> list:
        try:
            with open(self.path, 'rb') as file:
                self.scores = pickle.load(file)
        except FileNotFoundError:
            self.scores = []

    def draw(self, registro_actual, color_registro) -> None:
        Cursor.move_and_print([6, 2], f"{Color.RED}{Cursor.S_B}{f'💀 GAME OVER 💀':^{columns - 2}}{Cursor.S_R}")
        Cursor.move_and_print([7, 2], f"{'―――――――――――――――――――――――――――――――':^{columns - 1}}")

        # 10 MEJORES PUNTUACIONES
        ranking = sorted(self.scores, key=lambda score: score[2], reverse=True)
        for i, element in enumerate(ranking[:self.SCORE_MAX_LENGTH], 8):
            color = f"{Cursor.S_B}{color_registro}" if element[0] == registro_actual[0] else Cursor.S_R
            item = f"{f'🤖 {element[1]}':<15}{element[2]:>15}"
            Cursor.move_and_print([i, 2], f"{color}{item:^{columns - 2}}")

class Keyboard:
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    lock = threading.Lock()

    def start_keyboard(self):
        def read_keyboard():
            global key_pressed
            try:
                key_read=""
                tty.setcbreak(Keyboard.fd)
                while key_read != "q":
                    ch1 = sys.stdin.read(1)
                    if ch1 == '\x1b':
                        ch2 = sys.stdin.read(1)
                        ch3 = sys.stdin.read(1)
                        k = ch1 + ch2 + ch3
                        if k == '\x1b[A':
                            key_read = "U"
                        elif k == '\x1b[B':
                            key_read = "D"
                        elif k == '\x1b[C':
                            key_read = "R"
                        elif k == '\x1b[D':
                            key_read = "L"
                    elif ch1 in ['q', 'Q']:
                        key_read = "Q"   
                    elif ch1 in ['p', 'P']:
                        key_read = "P"
                    elif ch1 in ['+', '-']:
                        key_read = ch1
                    with Keyboard.lock:
                        key_pressed = key_read
            finally:
                termios.tcsetattr(Keyboard.fd, termios.TCSADRAIN, Keyboard.old_settings)
    
        key_thread = threading.Thread(target=read_keyboard, daemon=True)
        key_thread.start()
        return key_thread

class Game:
    MIN_SPEED = 1
    MAX_SPEED = 15
    USERNAME_MAX_LENGTH = 15
    FRAME_RATE = 0.05

    def __init__(self):
        self.username = ""
        self.speed = 5
        self._last_speed = self.speed
        self.score = 0
        self.in_pause = False
        self.action = "R"
        self._last_direction = self.action
    
    def _get_valid_username(self) -> str:
        Cursor.move_cursor(lines + 6, 0)
        new_username = input(f" {Cursor.SHOW}{Cursor.S_R}{Cursor.S_B}🤖 PLAYER NAME: {Cursor.S_R}{Color.GRAY}")

        # COMPROBAR SI LA LONGITUD DEL NOMBRE ES MAYOR DE LA MÁXIMA PERMITIDA
        if len(new_username) >= self.USERNAME_MAX_LENGTH:
            print(f"{Cursor.HIDE}{Color.RED}Username must be less than 15 characters{Cursor.S_R}")
            time.sleep(1)
            return ""
        print(Cursor.HIDE, end="")
        return new_username
    
    def change_speed(self) -> int:
        change = { '+': 1, '-': -1 }
        new_speed = self.speed + change[key_pressed]
        return new_speed if self.MIN_SPEED <= new_speed <= self.MAX_SPEED else self.speed
    
    def obtain_frame_rate(self) -> float:
        vertical_speed = 0.5 / self.speed
        horizontal_speed = 0.3 / self.speed 
        return vertical_speed if self.action in ['U', 'D'] else horizontal_speed
    
    def draw_info(self) -> None:
        width = (columns) // 3
        speed_text = self.speed if self.speed > 0 else f"{Color.RED}PAUSE{Cursor.S_R}  "

        # IMPRIMIR CADA INFO DEBAJO DEL MAPA Y ALINEARLO A LA ANCHURA A LA IZQUIERDA, CENTRO Y DERECHA
        Cursor.move_cursor(lines + 6, 0)
        print(f" {f'🐍 SCORE: {self.score}':<{width}}", end="")
        print(f"{f'🚀 SPEED: {speed_text}':^{width}}", end="")
        print(f"{f'🤖 {self.username}':>{width}}", end="")

        # ESTA LÍNEA SOLUCIONA UN PROBLEMA EN EL QUE NO SE CAMBIABA EL TEXTO AL ESTABLECER EL JUEGO EN PAUSE
        sys.stdout.flush()
    
    def get_username(self, map) -> None:
        while game.username == "":
            map.draw()
            self.username = self._get_valid_username()
    
    def get_current_action(self, keyboard, snake):
        with keyboard.lock:
            if key_pressed in ['U', 'L', 'D', 'R']:
                if not snake.is_invalid_move(key_pressed, self._last_direction):
                    snake.direction = key_pressed
                    self.action = key_pressed
            elif key_pressed in ['P', 'Q']:
                self.action = key_pressed

    def loop(self, keyboard: Keyboard, map: Map, snake: Snake, fruit: Fruit, scoreManager: ScoreManager) -> None:
        global key_pressed
        while True:
            self.get_current_action(keyboard, snake)

            # CONTROL DE PAUSA
            if self.in_pause:
                if self.action != 'P':
                    self.in_pause = False
                    self.speed = last_speed
                    self.draw_info()
                continue
            
            # CONTROL DE ACCIONES
            if self.action == 'Q':
                Game.end(scoreManager, map, record)
                break
            elif self.action == 'P':
                last_speed = self.speed
                self.speed = 0
                self.in_pause = True
                self.draw_info()
                continue
            elif key_pressed in ['+', '-']:
                self.speed = self.change_speed()
                self.draw_info()
                key_pressed = self._last_direction
                continue
            
            # MOVER SERPIENTE
            tail = snake.move(self._last_direction)

            # COMPROBAR SI SE COMIÓ UNA FRUTA
            if snake.check_eat(tail, fruit):
                snake.change_head_color(color=Color.LIGHT_GREEN, reset_color=True)
                range = map.get_valid_range(snake)
                fruit = Fruit(range)
                fruit.draw()
                self.score += 1
                self.draw_info()

            # COMPROBAR SI SE HA CHOCADO
            if snake.check_collision(map):
                record = scoreManager.save(self.username, self.score)
                snake.change_head_color(color=Color.RED, reset_color=False)
                Game.end(scoreManager, map, record)
                break

            # GUARDAR ÚLTIMA TECLA Y VELOCIDAD VÁLIDA
            self._last_direction = self.action
            self.last_speed = self.speed

            # TIEMPO DE ESPERA ENTRE CADA FOTOGRAMA
            frame_rate = self.obtain_frame_rate()
            time.sleep(frame_rate)
    
    @staticmethod
    def end(scoreManager, map, record: tuple = None) -> None:
        if record is not None:
            time.sleep(1)
            map.draw()
            scoreManager.draw(record, color_registro=Color.MAGENTA)
        else:
            map.draw()
            Cursor.move_and_print(((lines // 2) + 5, 2), f"{f'THANKS FOR PLAYING!':^{columns}}")

# ==========================================================================
# START
game = Game()
map = Map(15, 50)
snake = Snake(initial_position)
fruit = Fruit(map.get_valid_range(snake))

keyboard = Keyboard()
scoreManager = ScoreManager()
scoreManager.load()

try:
    # PEDIR ANTES DE EMPEZAR EL NOMBRE DE USUARIO.
    game.get_username(map)

    # DIBUJAR EN PANTALLA LOS ELEMENTOS.
    snake.draw()
    fruit.draw()
    game.draw_info()
    
    # INICIAR BUCLE DEL JUEGO.
    keyboard.start_keyboard()
    game.loop(keyboard, map, snake, fruit, scoreManager)
except KeyboardInterrupt:
    Game.end(scoreManager, map)
finally:
    termios.tcsetattr(Keyboard.fd, termios.TCSADRAIN, Keyboard.old_settings)
    Cursor.move_and_print((map.lines + 5, 0), f"{Cursor.SHOW}{Cursor.S_R}")
    sys.exit(1)
