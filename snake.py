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
# CONFIGURACIÓN DEL JUEGO
lines = 15                                      # MAP SIZE LINES
columns = 50                                    # MAP SIZE COLUMNS
in_pause = False

# --------------------------------------------------------------------------
# USUARIO Y PUNTUACIÓN
score = 0
SCORE_MAX_LENGTH = 10

# --------------------------------------------------------------------------
# TIEMPO Y VELOCIDAD
speed = 5
last_speed = 5
MIN_SPEED = 1
MAX_SPEED = 15
FRAME_RATE = 0.05
EAT_WAIT_TIME = 0.15

# --------------------------------------------------------------------------
# SNAKE
initial_position = [(10, 10), (10, 9), (10, 8), (10, 7)]
SNAKE_VERTICAL = f"█{S_R}"
SNAKE_HORIZONTAL = f"■{S_R}"
SNAKE_TURN = f"▮{S_R}"

# --------------------------------------------------------------------------
# VARIABLES DE TECLADO
key_pressed = "R"                               # USER LAST KEY PRESSED


# ==========================================================================
# CLASES
#
# Clases que usa el programa
# --------------------------------------------------------------------------
class Map:
    def __init__(self, lines, columns):
        self.lines = lines
        self.columns = columns

    def draw_map(self):
        # PINTAR EL BANNER.
        print(CLEAR_SCREEN, end="")
        print(f"""  ╔═╗╦ ╦╔╦╗╦ ╦╔═╗╔╗╔  ╔═╗╔╗╔╔═╗╦╔═╔═╗
  ╠═╝╚╦╝ ║ ╠═╣║ ║║║║  ╚═╗║║║╠═╣╠╩╗╠╣ 
  ╩   ╩  ╩ ╩ ╩╚═╝╝╚╝  ╚═╝╝╚╝╩ ╩╩ ╩╚═╝     {C_GRAY}DAW 2026""")

        # DIBUJAR EL MAPA CON SUS FILAS Y SOLUMNAS.
        print(f"▄"*(columns+2))
        print(f"█{' '*(columns)}█\n"*lines, end="")
        print(f"▀"*(columns+2))

        # DEVOLVER LOS LÍMITES DEL MAPA.
        return { "U": 4, "D": self.lines + 5, "L": 1, "R": self.columns + 2 }
    

class Snake:
    def __init__(self):
        self.position = initial_position[:]

    def draw_snake(self):
        for fila, columna in self.position:
            move_and_draw_char([fila, columna], f"{C_G}{SNAKE_HORIZONTAL}")
    
    def move_snake(self, direction, last_direction, head_color):
        head = self.position[0]
        tail = self.position.pop()

        # SUMARLE O RESTARLE 1 DEPENDIENDO DE LA DIRECCIÓN
        movement = { "U": (-1, 0), "D": (1, 0), "L": (0, -1), "R": (0, 1) }
        head = head[0] + movement[direction][0], head[1] + movement[direction][1]

        # AÑADIR LA NUEVA CABEZA
        self.position.insert(0, head)
        character = SNAKE_HORIZONTAL if direction in ['L', 'R'] else SNAKE_VERTICAL
        move_and_draw_char(head, f"{head_color}{character}")
        move_and_draw_char(self.position[1], f"{C_G}{character}")

        # COMPROBAR SI HA GIRADO Y MOSTRAR UN CARÁCTER DISTINTO EN LOS GIROS DEL CUERPO.
        if self.__is_turning(direction, last_direction):
            move_and_draw_char(self.position[1], f"{C_G}{SNAKE_TURN}")

        # BORRAR LA COLA PINTANDO UN ESPACIO EN BLANCO
        move_and_draw_char(tail, " ")
        return tail
    
    def get_valid_move(self, direction, last_direction):
        opposites = { 'U': 'D', 'D': 'U', 'L': 'R', 'R': 'L' }
        for case in opposites.keys():
            if direction == case and last_direction == opposites[case]:
                return last_direction
        return direction
    
    def change_head_color(self, direction, color, reset_color):
        head = self.position[0]
        character = SNAKE_HORIZONTAL if direction in ['L', 'R'] else SNAKE_VERTICAL
        move_and_draw_char(head, f"{color}{character}{S_R}")
        if reset_color:
            time.sleep(EAT_WAIT_TIME)
            move_and_draw_char(head, f"{C_G}{character}{S_R}")
    
    def __is_turning(self, direction, last_direction):
        vertical = ['U', 'D']
        horizontal = ['L', 'R']

        if direction in vertical and last_direction in horizontal:
            return True
        elif direction in horizontal and last_direction in vertical:
            return True

        return False
    
    def check_collision(self, map_limits):
        head = self.position[0]
        if head in self.position[1:] or not self.__in_limits(head, map_limits):
            return True
        
        return False
    
    def __in_limits(self, head, map_limits):
        if not map_limits['D'] > head[0] > map_limits['U']:
            return False
        elif not map_limits['L'] < head[1] < map_limits['R']:
            return False
        
        return True
    
    def add_tail(self, tail):
        self.position.append(tail)
        move_and_draw_char(tail, f"{C_G}■{S_R}")
    
    def __len__(self):
        return len(self.position)


class Fruit:
    def __init__(self, snake, map_limits):
        self.position = self.__get_position(snake, map_limits)
        self.color = self.__get_random_color()
        self.draw_fruit()

    def draw_fruit(self):
        move_and_draw_char(self.position, f"{self.color}⬤{S_R}")

    def __get_valid_range(self, snake, lines, columns):
        map_range = []
        for line in lines:
            for column in columns:
                coordenada = tuple([line, column])
                if coordenada not in snake.position:
                    map_range.append(coordenada)
        return map_range

    def __get_position(self, snake, map_limits):
        lines = list(range(map_limits['U'] + 1, map_limits['D']))
        columns = list(range(map_limits['L'] + 1, map_limits['R']))

        # GENERAR EL RANGO DE POSICIONES
        map_range = self.__get_valid_range(snake, lines, columns)
        self.position = (random.choice(map_range))
        return self.position
    
    def __get_random_color(self):
        colors = [C_G, C_LG, C_R, C_Y, C_LR, C_B, C_M, C_C, C_GRAY]
        return random.choice(colors)
    
    def check_eat(self, snake, tail):
        head = snake.position[0]
        if head == self.position:
            snake.add_tail(tail)
            return True
        return False


class User:
    USERNAME_MAX_LENGTH = 15
    total_users = []

    def __init__(self):
        self.name = ""
        self.score = 0
    
    def get_valid_name(self):
        # PEDIR NOMBRE DE USUARIO
        move_cursor(lines + 6, 0)
        new_username = input(f" {CURSOR_SHOW}{S_R}{S_B}🤖 PLAYER NAME: {S_R}{C_GRAY}")

        # COMPROBAR SI SU LONGITUD ES MAYOR DE LA MÁXIMA PERMITIDA
        if len(new_username) >= User.USERNAME_MAX_LENGTH:
            print(f"{CURSOR_HIDE}{C_R}Username must be less than 15 characters{S_R}")
            time.sleep(1)
            self.name = ""

        show_game_info(new_username)
        self.name = new_username


# ==========================================================================
# FUNCIONES
#
# Estas son todas las funciones que usa el programa
# --------------------------------------------------------------------------
# CAPTURA DEL TECLADO
def start_keyboard():
    def read_keyboard():
        global key_pressed
        try:
            key_read=""
            tty.setcbreak(fd)
            while key_read != "q":
                ch1 = sys.stdin.read(1)
                if ch1 == '\x1b':  # posible flecha
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
                elif ch1 == 'q':
                    key_read = "Q"
                # AÑADIR LA TECLA P PARA EL PAUSE.    
                elif ch1 == 'p':
                    key_read = "P"
                # AÑADIR LAS TECLAS + Y -
                elif ch1 == '+':
                    key_read = "+"
                elif ch1 == '-':
                    key_read = "-"
                with lock:
                    key_pressed = key_read                    
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
 
    key_thread = threading.Thread(target=read_keyboard, daemon=True)
    key_thread.start()
    return key_thread

# --------------------------------------------------------------------------
# COMENZAR EL JUEGO
def start_game():
    global score, nickname, speed, last_speed, key_pressed, in_pause

    def change_speed(action):
        # CAMBIAR LA VELOCIDAD Y COMPROBAR SI ESTÁ DENTRO DEL MÍNIMO Y MÁXIMO
        change = { '+': 1, '-': -1 }
        new_speed = speed + change[action]
        return new_speed if is_speed_valid(new_speed) else speed

    def is_speed_valid(new_speed):
        # COMPROBAR SI LA VELOCIDAD NUEVA ESTÁ ENTRE EL MÍNIMO Y MÁXIMO
        return MIN_SPEED <= new_speed <= MAX_SPEED
    
    def obtain_frame_rate(action):
        if action in ['U', 'D']:
            # HACER QUE SE REDUZCA UN POCO LA VELOCIDAD AL IR EN DIRECCIÓN VERTICAL
            return 0.5 / speed
        return 0.3 / speed

    # --------------------------------------------------------------------------
    try:
        User.total_users = load_scores()
        map = Map(lines, columns)

        # PEDIR ANTES DE EMPEZAR EL NOMBRE DE USUARIO
        user = User()
        while user.name == "":
            map_limits = map.draw_map()
            user.get_valid_name()

        # SERPIENTE
        snake = Snake()
        snake.draw_snake()

        # FRUTA
        fruit = Fruit(snake, map_limits)
        last_color = C_G

        # POR DEFECTO, LA PRIMERA TECLA SERÁ A LA DERECHA
        start_keyboard()
        last_key_pressed = 'R'
        print(CURSOR_HIDE, end="")

        while True:
            with lock:
                action = key_pressed

            # SI EL JUEGO ESTÁ PAUSADO, SALTAR ITERACIONES HASTA QUE NO CAPTURA UNA P
            if in_pause:
                if action != 'P':
                    in_pause = False
                    speed = last_speed
                    show_game_info(nickname)
                continue
            
            if action == 'Q':
                # CONTROLA LA PULSACIÓN DE LA LETRA Q PARA SALIR
                end_game(map, False)
            elif action == 'P':
                # GUARDAR ÚLTIMA VELOCIDAD Y ESTABLECERLA EN 0
                last_speed = speed
                speed = 0

                # MOSTRAR ESTADO EN PAUSE
                in_pause = True
                show_game_info(nickname)
                continue
            elif action in ['+', '-']:
                # CAMBIO DE VELOCIDAD
                speed = change_speed(action)
                show_game_info(nickname)

                # VOLVER A LA ÚLTIMA DIRECCIÓN VÁLIDA
                key_pressed = last_key_pressed
                continue
            
            # MOVER LA SERPIENTE A UNA DIRECCIÓN VÁLIDA Y GUARDAR LA POSICIÓN ANTERIOR DE LA COLA.
            action = snake.get_valid_move(action, last_key_pressed)
            tail = snake.move_snake(action, last_key_pressed, last_color)

            # COMPROBAR SI SE HA CHOCADO CON UNA FRUTA
            if fruit.check_eat(snake, tail):
                # CAMBIAR EL COLOR DE LA CABEZA
                # change_head_color(snake, action, color=C_LG, reset_color=True)
                last_color = fruit.color

                # PINTAR FRUTA NUEVA Y ACTUALIZAR SCORE
                fruit = Fruit(snake, map_limits)
                score = len(snake) - len(initial_position)
                show_game_info(nickname)

            # COMPROBAR SI SE HA CHOCADO
            if snake.check_collision(map_limits):
                snake.change_head_color(action, color=C_R, reset_color=False)
                end_game(map, True)

            # GUARDAR LA ÚLTIMA TECLA Y VELOCIDAD VÁLIDA
            last_key_pressed = action
            last_speed = speed

            # TIEMPO DE ESPERA ENTRE CADA FOTOGRAMA
            frame_rate = obtain_frame_rate(action)
            time.sleep(frame_rate)
    except KeyboardInterrupt:
        end_game(map, False)
        reset_terminal()


# --------------------------------------------------------------------------
# MOVER EL CURSOR DE LA TERMINAL A UNA POSICIÓN DETERMINADA:
def move_cursor(line, column):
    print(f"\033[{line};{column}H", end="")

def move_and_draw_char(position, char):
    # MOVER CURSOR A UNA POSICIÓN Y PINTAR UN CARACTER. ENCAPSULÉ ESTA FUNCIÓN PORQUE EL PATRÓN SE REPITE VARIAS VECES.
    move_cursor(*position)
    print(char)


# --------------------------------------------------------------------------
def show_game_info(username):
    # DIVIDIR LA ANCHURA DEL MAPA EN 3, YA QUE SE IMPRIMEN 3 STATS
    anchura = (columns) // 3

    # MOVER EL CURSOR DEBAJO DEL MAPA
    move_cursor(lines + 6, 0)

    # DEFINIR SI SE IMPRIME LA VELOCIDAD O PAUSE
    speed_text = speed if speed > 0 else f"{C_R}PAUSE{S_R}"

    # IMPRIMIR CADA STAT Y ALINEARLO A LA ANCHURA A LA IZQUIERDA, CENTRO Y DERECHA
    print(f" {f'🐍 SCORE: {score}':<{anchura}}", end="")
    print(f"{f'🚀 SPEED: {speed_text}':^{anchura}}", end="")
    print(f"{f'🤖 {username}':>{anchura}}", end="")

    # ESTA LÍNEA SOLUCIONA UN PROBLEMA EN EL QUE NO SE CAMBIABA EL TEXTO AL ESTABLECER EL JUEGO EN PAUSE
    sys.stdout.flush()


# --------------------------------------------------------------------------
def end_game(map, died):
    def show_thanks_text():
        map.draw_map()
        move_cursor((lines // 2) + 5, 2)
        print(f"{f'THANKS FOR PLAYING!':^{columns}}")

    if died:
        # SI EL JUGADOR MUERE, CARGA EN UN FICHERO EL HISTÓRICO DE LOS SCORES GUARDADOS POR CADA JUGADOR. DESPUÉS MOSTRAR PUNTUACIONES.
        registro = save_scores(User.total_users)
        time.sleep(1)
        show_scores(map, registro, color_registro=C_M)
    else:
        # MOSTRAR UN AGRADECIMIENTO SI SE HA SALIDO DEL JUEGO POR EL BOTÓN Q
        show_thanks_text()

    # ANTES DE SALIR DEL JUEGO RESTAURAR TECLADO:
    reset_terminal()


def reset_terminal():
    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    move_cursor(lines + 6, 0)
    print(CURSOR_SHOW, S_R, end="")
    sys.exit(1)


# --------------------------------------------------------------------------
def save_scores():
    # GUARDAR EL NUEVO REGISTRO EN LA LISTA DE SCORES
    registro = tuple((time.time(), nickname, score))
    User.total_users.append(registro)

    # GUARDA EN EL FICHERO scores.pkl LA LISTA DE SCORES
    with open('scores.pkl', 'wb') as file:
        pickle.dump(User.total_users, file)

    # DEVOLVER EL REGISTRO ACTUAL
    return registro


def load_scores():
    try:
        with open('scores.pkl', 'rb') as file:
            return pickle.load(file)
    except FileNotFoundError:
        return []


# --------------------------------------------------------------------------
def show_scores(map, registro_actual, color_registro):
    map.draw_map()
    move_and_draw_char([6, 2], f"{C_R}{S_B}{f'💀 GAME OVER 💀':^{columns - 2}}{S_R}")
    move_and_draw_char([7, 2], f"{'―――――――――――――――――――――――――――――――':^{columns - 1}}")

    # ORDENAR DE MAYOR PUNTUACIÓN A MENOR PUNTUACIÓN LOS 10 MEJORES
    current_line = 7
    ranking = sorted(User.total_users, key=lambda score: score[2], reverse=True)
    for element in ranking[:SCORE_MAX_LENGTH]:
        # RESALTAR EN COLOR DISTINTO LA PARTIDA ACTUAL, SI COINCIDE LA FECHA DEL REGISTRO CON LA FECHA DEL ACTUAL
        color = f"{S_B}{color_registro}" if element[0] == registro_actual[0] else S_R
        current_line += 1
        item = f"{f'🤖 {element[1]}':<15}{element[2]:>15}"
        move_and_draw_char([current_line, 2], f"{color}{item:^{columns - 2}}")


# ==========================================================================
# EMPEZAR EL JUEGO
# 
# Aquí empieza el código del programa
fd = sys.stdin.fileno()
old_settings = termios.tcgetattr(fd)
lock = threading.Lock()

start_game()
