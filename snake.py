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
# CURSOR DEL TERMINAL
CURSOR_HIDE="\033[?25l"                         # HIDE CURSOR
CURSOR_SHOW="\033[?25h"                         # SHOW CURSOR
CLEAR_SCREEN="\033c"                            # CLEAR SCREEN
S_R="\033[0m"                                   # STYLE RESET
S_D="\033[2m"                                   # STYLE DIM
S_B="\033[1m"                                   # STYLE BOLD
R_L="\033[2K"                                   # REMOVE LINE
M_U="\033[A"                                    # MOVE UP 1 LINE

# --------------------------------------------------------------------------
# COLORES
C_G="\033[32m"                                  # COLOR GREEN
C_LG="\033[92m"                                 # COLOR LIGHT GREEN
C_R="\033[31m"                                  # COLOR RED
C_Y="\033[33m"                                  # COLOR YELLOW
C_LR="\033[91m"                                 # COLOR LIGHT RED
C_B="\033[34m"                                  # COLOR BLUE
C_M="\033[35m"                                  # COLOR MAGENTA
C_C="\033[36m"                                  # COLOR CYAN
C_GRAY="\033[37m"                               # COLOR GRAY

# --------------------------------------------------------------------------
# USUARIO Y PUNTUACIÓN
SCORE_MAX_LENGTH = 10

# --------------------------------------------------------------------------
# SNAKE
initial_position = [(10, 10), (10, 9), (10, 8), (10, 7)]

# --------------------------------------------------------------------------
# VARIABLES DE TECLADO
key_pressed = "R"                               # USER LAST KEY PRESSED


# ==========================================================================
# CLASES
#
class Drawable(ABC):
    @abstractmethod
    def draw(self):
        pass


class Game:
    MIN_SPEED = 1
    MAX_SPEED = 15
    USERNAME_MAX_LENGTH = 15
    FRAME_RATE = 0.05

    def __init__(self):
        self.username = self.__get_valid_username()
        self.speed = 5
        self.score = 0
        self.in_pause = False
        self.action = "R"
    
    def __get_valid_username(self) -> str:
        # PEDIR NOMBRE DE USUARIO
        move_cursor(lines + 6, 0)
        new_username = input(f" {CURSOR_SHOW}{S_R}{S_B}🤖 PLAYER NAME: {S_R}{C_GRAY}")

        # COMPROBAR SI SU LONGITUD ES MAYOR DE LA MÁXIMA PERMITIDA
        if len(new_username) >= self.USERNAME_MAX_LENGTH:
            print(f"{CURSOR_HIDE}{C_R}Username must be less than 15 characters{S_R}")
            time.sleep(1)
            return ""
        print(CURSOR_HIDE, end="")
        return new_username
    
    def change_speed(self) -> int:
        change = { '+': 1, '-': -1 }
        new_speed = self.speed + change[self.action]
        return new_speed if self.MIN_SPEED <= new_speed <= self.MAX_SPEED else self.speed
    
    def obtain_frame_rate(self) -> float:
        vertical_speed = 0.5 / self.speed
        horizontal_speed = 0.3 / self.speed 
        return vertical_speed if self.action in ['U', 'D'] else horizontal_speed
    
    def show_game_info(self) -> None:
        """Esta funcion imprime el Score, la velocidad del juego, y el nombre de usuario debajo del mapa"""
        width = (columns) // 3
        speed_text = self.speed if self.speed > 0 else f"{C_R}PAUSE{S_R}  "

        # IMPRIMIR CADA INFO DEBAJO DEL MAPA Y ALINEARLO A LA ANCHURA A LA IZQUIERDA, CENTRO Y DERECHA
        move_cursor(lines + 6, 0)
        print(f" {f'🐍 SCORE: {self.score}':<{width}}", end="")
        print(f"{f'🚀 SPEED: {self.speed_text}':^{width}}", end="")
        print(f"{f'🤖 {self.username}':>{width}}", end="")

        # ESTA LÍNEA SOLUCIONA UN PROBLEMA EN EL QUE NO SE CAMBIABA EL TEXTO AL ESTABLECER EL JUEGO EN PAUSE
        sys.stdout.flush()
    
    def end_game(self, map, record: tuple = None) -> None:
        if record is not None:
            time.sleep(1)
            map.draw()
            self.show_scores(record, color_registro=C_M)
        else:
            map.draw()
            move_and_print(((lines // 2) + 5, 2), f"{f'THANKS FOR PLAYING!':^{columns}}")


class Map(Drawable):
    def __init__(self, lines, columns):
        self.lines = lines
        self.columns = columns
        self.banner = f"""  ╔═╗╦ ╦╔╦╗╦ ╦╔═╗╔╗╔  ╔═╗╔╗╔╔═╗╦╔═╔═╗
    ╠═╝╚╦╝ ║ ╠═╣║ ║║║║  ╚═╗║║║╠═╣╠╩╗╠╣ 
    ╩   ╩  ╩ ╩ ╩╚═╝╝╚╝  ╚═╝╝╚╝╩ ╩╩ ╩╚═╝     {C_GRAY}DAW 2026"""
        
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
        print(CLEAR_SCREEN, end="")
        print(self.banner)

        print(f"▄" * (self.columns + 2))
        print(f"█{' ' * (self.columns)}█\n" * self.lines, end="")
        print(f"▀" * (self.columns + 2))


class Snake(Drawable):
    symbol = { "VERTICAL": f"█{S_R}", "HORIZONTAL": f"■{S_R}", "TURN": f"▮{S_R}" }
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
        newHead = self.head + movement[self.direction][0], self.head + movement[self.direction][1]
        self.body.insert(0, newHead)

        # PINTAR NUEVA CABEZA.
        character = self.symbol["HORIZONTAL"] if self.direction in ['L', 'R'] else self.symbol["VERTICAL"]
        move_and_print(self.head, f"{C_G}{character}")

        # COMPROBAR SI HA GIRADO.
        if self.is_turning(last_direction):
            move_and_print(self.body[1], f"{C_G}{self.symbol["TURN"]}")

        # BORRAR LA COLA.
        tail = self.body.pop()
        move_and_print(tail, " ")
        return tail
    
    def check_collision(self) -> bool:
        if self.head in self.body[1:] or not self.in_limits:
            return True
        return False
    
    def check_eat(self, tail, fruit_position) -> bool:
        if self.head == fruit_position:
            self.body.append(tail)
            move_and_print(tail, f"{C_G}■{S_R}")
            return True
        return False
    
    def get_valid_move(self, last_direction) -> str:
        opposites = { 'U': 'D', 'D': 'U', 'L': 'R', 'R': 'L' }
        for case in opposites.keys():
            if self.direction == case and last_direction == opposites[case]:
                return last_direction
        return self.direction
    
    @property
    def in_limits(self) -> bool:
        if not self.limits['D'] > self.head > self.limits['U']:
            return False
        elif not self.limits['L'] < self.head < self.limits['R']:
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
        move_and_print(self.head, f"{color}{character}{S_R}")
        if reset_color:
            time.sleep(self.EAT_WAIT_TIME)
            move_and_print(self.head, f"{C_G}{character}{S_R}")
    
    def draw(self) -> None:
        for fila, columna in self.body:
            move_and_print([fila, columna], f"{C_G}{self.symbol["HORIZONTAL"]}")


class Fruit(Drawable):
    symbol = f"⬤{S_R}"

    def __init__(self, position):
        self._position = position
        self.color = self.__get_random_color()
    
    @property
    def position(self):
        return self._position
    
    @position.setter
    def position(self, value):
        self._position = value
    
    def __get_random_color() -> str:
        colors = [C_G, C_LG, C_R, C_Y, C_LR, C_B, C_M, C_C, C_GRAY]
        return random.choice(colors)
    
    def draw(self, valid_range) -> tuple:
        # TODO: OBTENER EL RANGO VÁLIDO DE POSICION
        # Map.get_valid_range(snake)
        self.position = (random.choice(valid_range))
        color = self.__get_random_color()
        move_and_print(self.position, f"{color}{self.symbol}")
    

class ScoreManager(Drawable):
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
                return pickle.load(file)
        except FileNotFoundError:
            return []

    def draw(self, registro_actual, color_registro) -> None:
        move_and_print([6, 2], f"{C_R}{S_B}{f'💀 GAME OVER 💀':^{columns - 2}}{S_R}")
        move_and_print([7, 2], f"{'―――――――――――――――――――――――――――――――':^{columns - 1}}")

        # 10 MEJORES PUNTUACIONES
        ranking = sorted(self.scores, key=lambda score: score[2], reverse=True)
        for i, element in enumerate(ranking[:SCORE_MAX_LENGTH], 8):
            color = f"{S_B}{color_registro}" if element[0] == registro_actual[0] else S_R
            item = f"{f'🤖 {element[1]}':<15}{element[2]:>15}"
            move_and_print([i, 2], f"{color}{item:^{columns - 2}}")


class Keyboard:
    def start_keyboard():
        def read_keyboard():
            global key_pressed
            try:
                key_read=""
                tty.setcbreak(fd)
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
                    # AÑADIR LA TECLA P PARA EL PAUSE.    
                    elif ch1 in ['p', 'P']:
                        key_read = "P"
                    # AÑADIR LAS TECLAS + Y -
                    elif ch1 in ['+', '-']:
                        key_read = ch1
                    with lock:
                        key_pressed = key_read                    
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    
        key_thread = threading.Thread(target=read_keyboard, daemon=True)
        key_thread.start()
        return key_thread
        

# ==========================================================================
# FUNCIONES
#
# Estas son todas las funciones que usa el programa
# --------------------------------------------------------------------------
# COMENZAR EL JUEGO
def start_game():
    global key_pressed
    try:
        # INICIZALIZAR VARIABLES
        username = ""
        speed = 5
        last_speed = 5
        score = 0
        in_pause = False
        snake = initial_position[:]

        # PEDIR ANTES DE EMPEZAR EL NOMBRE DE USUARIO
        while username == "":
            # PINTAR EL MAPA. SE GUARDAN SUS LÍMITES EN UNA VARIABLE.
            map_limits = draw_map()
            username = get_valid_username()

        # DIBUJAR LA SERPIETE, LA FRUTA Y LA INFORMACIÓN DE USUARIO
        draw_snake(snake)
        fruit = draw_fruit(snake, map_limits)
        show_game_info(username, score, speed)

        # POR DEFECTO, LA PRIMERA TECLA SERÁ A LA DERECHA
        start_keyboard()
        last_key_pressed = 'R'

        while True:
            with lock:
                action = get_valid_move(key_pressed, last_key_pressed)

            # CONTROL DE PAUSA
            if in_pause:
                if action != 'P':
                    in_pause = False
                    speed = last_speed
                    show_game_info(username, score, speed)
                continue
            
            # CONTROL DE ACCIONES
            if action == 'Q':
                # SALIR
                end_game()
                break
            elif action == 'P':
                # PAUSA
                last_speed = speed
                speed = 0
                in_pause = True
                show_game_info(username, score, speed)
                continue
            elif action in ['+', '-']:
                # CAMBIAR VELOCIDAD
                speed = change_speed(speed, action)
                show_game_info(username, score, speed)
                key_pressed = last_key_pressed
                continue
            
            # MOVER LA SERPIENTE A UNA DIRECCIÓN VÁLIDA Y GUARDAR LA POSICIÓN ANTERIOR DE LA COLA.
            tail = move_snake(snake, action, last_key_pressed)

            # COMPROBAR SI SE COMIÓ UNA FRUTA
            if check_eat(snake, tail, fruit):
                # CAMBIAR EL COLOR DE LA CABEZA
                change_head_color(snake, action, color=C_LG, reset_color=True)

                # PINTAR FRUTA NUEVA Y ACTUALIZAR SCORE
                fruit = draw_fruit(snake, map_limits)
                score += 1
                show_game_info(username, score, speed)

            # COMPROBAR SI SE HA CHOCADO
            if check_collision(snake, map_limits):
                scores = load_scores()
                record = save_scores(username, score, scores)
                change_head_color(snake, action, color=C_R, reset_color=False)
                end_game(record)
                break

            # GUARDAR LA ÚLTIMA TECLA Y VELOCIDAD VÁLIDA
            last_key_pressed = action
            last_speed = speed

            # TIEMPO DE ESPERA ENTRE CADA FOTOGRAMA
            frame_rate = obtain_frame_rate(speed, action)
            time.sleep(frame_rate)
    except KeyboardInterrupt:
        end_game()
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        move_cursor(lines + 6, 0)
        print(f"{CURSOR_SHOW}{S_R}", end="")
        sys.exit(1)


# --------------------------------------------------------------------------
# MOVER EL CURSOR DE LA TERMINAL A UNA POSICIÓN DETERMINADA:
def move_cursor(line: int, column: int) -> None:
    print(f"\033[{line};{column}H", end="")

# ENCAPSULÉ ESTA FUNCIÓN PORQUE EL PATRÓN SE REPITE VARIAS VECES.
def move_and_print(position: tuple, text: str) -> None:
    move_cursor(*position)
    print(text)


# ==========================================================================
# EMPEZAR EL JUEGO
# 
# Aquí empieza el código del programa
fd = sys.stdin.fileno()
old_settings = termios.tcgetattr(fd)
lock = threading.Lock()

start_game()
