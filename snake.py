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

# --------------------------------------------------------------------------
# USUARIO Y PUNTUACIÓN
USERNAME_MAX_LENGTH = 15
SCORE_MAX_LENGTH = 10

# --------------------------------------------------------------------------
# TIEMPO Y VELOCIDAD
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

def get_valid_username() -> str:
    # PEDIR NOMBRE DE USUARIO
    move_cursor(lines + 6, 0)
    new_username = input(f" {CURSOR_SHOW}{S_R}{S_B}🤖 PLAYER NAME: {S_R}{C_GRAY}")

    # COMPROBAR SI SU LONGITUD ES MAYOR DE LA MÁXIMA PERMITIDA
    if len(new_username) >= USERNAME_MAX_LENGTH:
        print(f"{CURSOR_HIDE}{C_R}Username must be less than 15 characters{S_R}")
        time.sleep(1)
        return ""
    print(CURSOR_HIDE, end="")
    return new_username
    
def get_valid_move(direction: str, last_direction: str) -> str:
    opposites = { 'U': 'D', 'D': 'U', 'L': 'R', 'R': 'L' }
    for case in opposites.keys():
        if direction == case and last_direction == opposites[case]:
            return last_direction
    return direction

def change_speed(speed: int, action: str) -> int:
    # CAMBIAR LA VELOCIDAD Y COMPROBAR SI ESTÁ DENTRO DEL MÍNIMO Y MÁXIMO
    change = { '+': 1, '-': -1 }
    new_speed = speed + change[action]
    return new_speed if MIN_SPEED <= new_speed <= MAX_SPEED else speed

def obtain_frame_rate(speed: int, action: str) -> float:
    # HACER QUE SE REDUZCA UN POCO LA VELOCIDAD AL IR EN DIRECCIÓN VERTICAL
    vertical_speed = 0.5 / speed
    horizontal_speed = 0.3 / speed 
    return vertical_speed if action in ['U', 'D'] else horizontal_speed


# --------------------------------------------------------------------------
# DIBUJAR EL MAPA.
def draw_map() -> dict:
    """Pinta el mapa en la pantalla y devuelve los límites del mapa"""
    print(CLEAR_SCREEN, end="")
    print(f"""  ╔═╗╦ ╦╔╦╗╦ ╦╔═╗╔╗╔  ╔═╗╔╗╔╔═╗╦╔═╔═╗
  ╠═╝╚╦╝ ║ ╠═╣║ ║║║║  ╚═╗║║║╠═╣╠╩╗╠╣ 
  ╩   ╩  ╩ ╩ ╩╚═╝╝╚╝  ╚═╝╝╚╝╩ ╩╩ ╩╚═╝     {C_GRAY}DAW 2026""")

    # DIBUJAR EL MAPA CON SUS FILAS Y SOLUMNAS.
    print(f"▄"*(columns+2))
    print(f"█{' '*(columns)}█\n"*lines, end="")
    print(f"▀"*(columns+2))

    # DEVOLVER UN DICCIONARIO CON LOS LÍMITES DEL MAPA.
    return { "U": 4, "D": lines + 5, "L": 1, "R": columns + 2 }


# --------------------------------------------------------------------------
# MOVER EL CURSOR DE LA TERMINAL A UNA POSICIÓN DETERMINADA:
def move_cursor(line: int, column: int) -> None:
    """Move cursor to specified terminal line and column"""
    print(f"\033[{line};{column}H", end="")

# ENCAPSULÉ ESTA FUNCIÓN PORQUE EL PATRÓN SE REPITE VARIAS VECES.
def move_and_print(position: tuple, text: str) -> None:
    """Mueve el cursor e imprime texto"""
    move_cursor(*position)
    print(text)


# --------------------------------------------------------------------------
# DIBUJAR LA SERPIENTE:
def draw_snake(snake: list) -> None:
    """Dado a una lista de tuplas, dibuja, para cada coordenada, el cuerpo de la serpiente"""
    for fila, columna in snake:
        move_and_print([fila, columna], f"{C_G}{SNAKE_HORIZONTAL}")


# MOVER LA SERPIENTE:
def move_snake(snake: list, direction: str, last_direction: str) -> tuple:
    """Mueve la serpiente a una dirección válida. Devuelve la cola eliminada en cada movimiento"""
    # OBTENER LAS COORDENADAS DE LA CABEZA Y LA COLA.
    head = snake[0]
    tail = snake.pop()

    # CALCULAR LA NUEVA POSICIÓN DE LA CABEZA E INSERTARLA AL PRINCIPIO
    movement = { "U": (-1, 0), "D": (1, 0), "L": (0, -1), "R": (0, 1) }
    head = head[0] + movement[direction][0], head[1] + movement[direction][1]
    snake.insert(0, head)

    # PINTAR LA NUEVA CABEZA DEPENDIENDO DEL MOVIMIENTO.
    character = SNAKE_HORIZONTAL if direction in ['L', 'R'] else SNAKE_VERTICAL
    move_and_print(head, f"{C_G}{character}")

    # COMPROBAR SI HA GIRADO Y MOSTRAR UN CARÁCTER DISTINTO EN LOS GIROS DEL CUERPO.
    if is_turning(direction, last_direction):
        move_and_print(snake[1], f"{C_G}{SNAKE_TURN}")

    # BORRAR LA COLA Y DEVOLVER SU POSICIÓN PARA USARLA LUEGO.
    move_and_print(tail, " ")
    return tail


def is_turning(direction: str, last_direction: str) -> bool:
    """Indica si se ha realizado cualquier giro"""
    vertical = ['U', 'D']
    horizontal = ['L', 'R']

    # SI SE HA GIRADO EL EJE ACTUAL CAMBIA CON RESPECTO AL ANTERIOR
    if direction in vertical and last_direction in horizontal:
        return True
    elif direction in horizontal and last_direction in vertical:
        return True
        
    # NO SE HA GIRADO
    return False

def change_head_color(snake: list, direction: str, color: str, reset_color: bool) -> None:
    # OBTENER LA CABEZA Y CAMBIAR DE COLOR
    head = snake[0]
    character = SNAKE_HORIZONTAL if direction in ['L', 'R'] else SNAKE_VERTICAL
    move_and_print(head, f"{color}{character}{S_R}")
    
    # VOLVER A RESETEAR EL COLOR SI SE PIDE
    if reset_color:
        time.sleep(EAT_WAIT_TIME)
        move_and_print(head, f"{C_G}{character}{S_R}")

# --------------------------------------------------------------------------
# SI EL JUGADOR SE HA CHOCADO
def check_collision(snake: list, map_limits: dict) -> bool:
    """Comprueba si la serpiente se ha chocado"""
    head_position = snake[0]
    if head_position in snake[1:] or not in_limits(head_position, map_limits):
        return True
    return False

def in_limits(head: tuple, map_limits: dict) -> bool:
    """Comprueba si la cabeza de la seripente está dentro del mapa"""
    # SI LA POSICIÓN VERTICAL DE LA CABEZA ESTÁ FUERA DE LOS LÍMITES DEL MAPA:
    if not map_limits['D'] > head[0] > map_limits['U']:
        return False
    # SI LA POSICIÓN HORIZONTAL DE LA CABEZA ESTÁ FUERA DE LOS LÍMITES DEL MAPA:
    elif not map_limits['L'] < head[1] < map_limits['R']:
        return False
        
    # ESTÁ DENTRO DE LOS LÍMITES
    return True


# --------------------------------------------------------------------------
def draw_fruit(snake: list, map_limits: dict) -> tuple:
    """Pinta una fruta en la pantalla en una coordenada aleatoria dentro de los límites del mapa y fuera del cuerpo de la serpiente"""
    # GUARDAR EL RANGO HORIZONTAL Y VERTICAL DEL MAPA:
    lines = list(range(map_limits['U'] + 1, map_limits['D']))
    columns = list(range(map_limits['L'] + 1, map_limits['R']))

    # GENERAR EL RANGO DE POSICIONES DONDE PUEDE CREARSE UNA FRUTA
    map_range = get_valid_range(snake, lines, columns)

    # MOVER EL CURSOR A UNA POSICIÓN ALEATORIA DENTRO DE MAP_RANGE Y PINTAR LA FRUTA.
    fruit_position = (random.choice(map_range))
    color = get_random_color()
    move_and_print(fruit_position, f"{color}⬤{S_R}")

    # DEVOLVER LA POSICIÓN DE LA FRUTA CREADA:
    return fruit_position

def get_valid_range(snake: list, lines: int, columns: int) -> list:
    """Obtiene una lista de tuplas con las coordenadas del mapa disponibles para crear una fruta nueva"""
    map_range = []
    for line in lines:
        for column in columns:
            coordenada = tuple([line, column])
            # FILTRAR LAS POSICIONES DONDE SE UBIQUE EL CUERPO DE LA SERPIENTE
            if coordenada not in snake:
                map_range.append(coordenada)
    return map_range

def get_random_color() -> str:
    """Obtiene un color aleatorio de la paleta de colores"""
    colors = [C_G, C_LG, C_R, C_Y, C_LR, C_B, C_M, C_C, C_GRAY]
    return random.choice(colors)


# --------------------------------------------------------------------------
def check_eat(snake: list, tail: tuple, fruit_position: tuple) -> bool:
    """Comprueba si las coordenadas de la cabeza de la serpiente coinciden con las de la fruta."""
    # SI LAS COORDENADAS DE LA CABEZA COINCIDEN CON LAS DE LA FRUTA
    head_position = snake[0]
    if head_position == fruit_position:
        # AÑADIR Y PINTAR LA COLA
        snake.append(tail)
        move_and_print(tail, f"{C_G}■{S_R}")
        return True
    return False


# --------------------------------------------------------------------------
def show_game_info(username: str, score: int, speed: int) -> None:
    """Esta funcion imprime el Score, la velocidad del juego, y el nombre de usuario debajo del mapa"""
    width = (columns) // 3
    speed_text = speed if speed > 0 else f"{C_R}PAUSE{S_R}  "

    # IMPRIMIR CADA INFO DEBAJO DEL MAPA Y ALINEARLO A LA ANCHURA A LA IZQUIERDA, CENTRO Y DERECHA
    move_cursor(lines + 6, 0)
    print(f" {f'🐍 SCORE: {score}':<{width}}", end="")
    print(f"{f'🚀 SPEED: {speed_text}':^{width}}", end="")
    print(f"{f'🤖 {username}':>{width}}", end="")

    # ESTA LÍNEA SOLUCIONA UN PROBLEMA EN EL QUE NO SE CAMBIABA EL TEXTO AL ESTABLECER EL JUEGO EN PAUSE
    sys.stdout.flush()


# --------------------------------------------------------------------------
def end_game(record: tuple = None) -> None:
    if record is not None:
        # SI EL JUGADOR MUERE, CARGA EN UN FICHERO EL HISTÓRICO DE LOS SCORES GUARDADOS POR CADA JUGADOR. DESPUÉS MOSTRAR PUNTUACIONES.
        time.sleep(1)
        draw_map()
        show_scores(record, color_registro=C_M)
    else:
        # MOSTRAR UN AGRADECIMIENTO SI SE HA SALIDO DEL JUEGO POR EL BOTÓN Q
        draw_map()
        move_and_print(((lines // 2) + 5, 2), f"{f'THANKS FOR PLAYING!':^{columns}}")


# --------------------------------------------------------------------------
def save_scores(username: str, score: int, scores: list) -> tuple:
    # GUARDAR EL NUEVO REGISTRO EN LA LISTA DE SCORES
    registro = tuple((time.time(), username, score))
    scores.append(registro)

    # GUARDA EN EL FICHERO scores.pkl LA LISTA DE SCORES
    with open('scores.pkl', 'wb') as file:
        pickle.dump(scores, file)
        return registro


def load_scores() -> list:
    # CARGA EL FICHERO scores.pkl (SI EXISTE)
    try:
        with open('scores.pkl', 'rb') as file:
            return pickle.load(file)
    # SI NO EXISTE EL FICHERO, LA LISTA DE SCORES SE QUEDA VACÍA
    except FileNotFoundError:
        return []


# --------------------------------------------------------------------------
def show_scores(registro_actual: tuple, color_registro) -> None:
    # IMPRIMIR GAME OVER
    move_and_print([6, 2], f"{C_R}{S_B}{f'💀 GAME OVER 💀':^{columns - 2}}{S_R}")
    move_and_print([7, 2], f"{'―――――――――――――――――――――――――――――――':^{columns - 1}}")

    # ORDENAR DE MAYOR PUNTUACIÓN A MENOR PUNTUACIÓN LOS 10 MEJORES
    scores = load_scores()
    ranking = sorted(scores, key=lambda score: score[2], reverse=True)
    for i, element in enumerate(ranking[:SCORE_MAX_LENGTH], 8):
        # IMPRIMIR CADA REGISTRO Y RESALTAR EN COLOR DISTINTO LA PARTIDA ACTUAL
        color = f"{S_B}{color_registro}" if element[0] == registro_actual[0] else S_R
        item = f"{f'🤖 {element[1]}':<15}{element[2]:>15}"
        move_and_print([i, 2], f"{color}{item:^{columns - 2}}")


# ==========================================================================
# EMPEZAR EL JUEGO
# 
# Aquí empieza el código del programa
fd = sys.stdin.fileno()
old_settings = termios.tcgetattr(fd)
lock = threading.Lock()

start_game()
