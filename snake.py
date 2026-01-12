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
nickname = ""
USERNAME_MAX_LENGTH = 15

score = 0
SCORE_MAX_LENGTH = 10
all_scores = []

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
# FUNCIONES
#
# Estas son todas las funciones que usa el programa
# --------------------------------------------------------------------------
# CAPTURA DEL TECLADO
def start_keyboard():
    """
    Capture keystrokes in background using threads:
        Q, P, UP, DOWN, LEFT, RIGHT: save key value in {key_pressed} variable
        +, -: modify {speed} variable in 0.05 steeps
 
    GLOBAL VARIABLES MODIFIED
      {key_pressed}
    """
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


# COMENZAR EL JUEGO
def start_game():
    global score, all_scores, nickname, speed, last_speed, key_pressed, in_pause

    # CARGAR LAS PUNTUACIONES DEL FICHERO SI EXISTE
    all_scores = load_scores()

    # PEDIR ANTES DE EMPEZAR EL NOMBRE DE USUARIO
    while nickname == "":
        # PINTAR EL MAPA. SE GUARDAN SUS LÍMITES EN UNA VARIABLE.
        map_limits = draw_map()
        nickname = get_valid_username()

    # DIBUJAR LA SERPIETE Y LA FRUTA
    snake = initial_position[:]
    draw_snake(snake)
    fruit = draw_fruit(snake, map_limits)

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
            end_game(False)
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
        action = get_valid_move(action, last_key_pressed)
        tail = move_snake(snake, action, last_key_pressed)

        # COMPROBAR SI SE HA CHOCADO CON UNA FRUTA
        if check_eat(snake, tail, fruit):
            # CAMBIAR EL COLOR DE LA CABEZA
            change_head_color(snake, action, color=C_LG, reset_color=True)

            # PINTAR FRUTA NUEVA Y ACTUALIZAR SCORE
            fruit = draw_fruit(snake, map_limits)
            score = len(snake) - len(initial_position)
            show_game_info(nickname)

        # COMPROBAR SI SE HA CHOCADO
        if check_collision(snake, map_limits):
            change_head_color(snake, action, color=C_R, reset_color=False)
            end_game(True)

        # GUARDAR LA ÚLTIMA TECLA Y VELOCIDAD VÁLIDA
        last_key_pressed = action
        last_speed = speed

        # TIEMPO DE ESPERA ENTRE CADA FOTOGRAMA
        frame_rate = obtain_frame_rate(action)
        time.sleep(frame_rate)


def get_valid_username():
    """
    Solicita el nombre y comprueba que sea menor o igual que el máximo número de carácteres permitidos.
    Devuelve: el nombre, si es válido. Si no: cadena vacía.
    """
    # PEDIR NOMBRE DE USUARIO
    move_cursor(lines + 6, 0)
    new_username = input(f" {CURSOR_SHOW}{S_R}🤖 PLAYER NAME: {C_GRAY}")

    # COMPROBAR SI SU LONGITUD ES MAYOR DE LA MÁXIMA PERMITIDA
    if len(new_username) >= USERNAME_MAX_LENGTH:
        print(f"{CURSOR_HIDE}{C_R}Username must be less than 15 characters{S_R}")
        time.sleep(1)
        return ""
    show_game_info(new_username)
    return new_username


def get_valid_move(direction, last_direction):
    """
    Devuelve si un giro es válido, no son válidos los de 180º
    """
    opposites = { 'U': 'D', 'D': 'U', 'L': 'R', 'R': 'L' }
    for case in opposites.keys():
        if direction == case and last_direction == opposites[case]:
            return last_direction
    return direction


def change_speed(action):
    """
    Aumenta o reduce la velocidad. Devuelve la velocidad cambiada si está dentro del mínimo y máximo.
    En caso contrario, no se cambia.
    """
    # CAMBIAR LA VELOCIDAD Y COMPROBAR SI ESTÁ DENTRO DEL MÍNIMO Y MÁXIMO
    change = { '+': 1, '-': -1 }
    new_speed = speed + change[action]
    return new_speed if is_speed_valid(new_speed) else speed


def is_speed_valid(new_speed):
    # COMPROBAR SI LA VELOCIDAD NUEVA ESTÁ ENTRE EL MÍNIMO Y MÁXIMO
    return MIN_SPEED <= new_speed <= MAX_SPEED


# --------------------------------------------------------------------------
# DIBUJAR EL MAPA.
def draw_map():
    """
    Pinta el mapa en la pantalla y devuelve los límites del mapa
    """
    # PINTAR EL BANNER.
    print(CLEAR_SCREEN, end="")
    print(f"""  ╔═╗╦ ╦╔╦╗╦ ╦╔═╗╔╗╔  ╔═╗╔╗╔╔═╗╦╔═╔═╗
  ╠═╝╚╦╝ ║ ╠═╣║ ║║║║  ╚═╗║║║╠═╣╠╩╗╠╣ 
  ╩   ╩  ╩ ╩ ╩╚═╝╝╚╝  ╚═╝╝╚╝╩ ╩╩ ╩╚═╝     {C_GRAY}DAW 2025""")

    # DIBUJAR EL MAPA CON SUS FILAS Y SOLUMNAS.
    print(f"▄"*(columns+2))
    print(f"█{' '*(columns)}█\n"*lines, end="")
    print(f"▀"*(columns+2))

    # DEVOLVER UN DICCIONARIO CON LOS LÍMITES DEL MAPA.
    return { "U": 4, "D": lines + 5, "L": 1, "R": columns + 2 }


# --------------------------------------------------------------------------
# MOVER EL CURSOR DE LA TERMINAL A UNA POSICIÓN DETERMINADA:
def move_cursor(line, column):
    """
    Move cursor to specified terminal line and column
    """
    print(f"\033[{line};{column}H", end="")


def move_and_draw_char(position, char):
    """
    Mueve el cursor y dibuja un carácter en esa posición
    """
    move_cursor(*position)
    print(char)


# --------------------------------------------------------------------------
# DIBUJAR LA SERPIENTE:
def draw_snake(snake):
    """
    Dado a una lista de tuplas, dibuja, para cada coordenada, el cuerpo de la serpiente
    """
    for fila, columna in snake:
        move_and_draw_char([fila, columna], f"{C_G}{SNAKE_HORIZONTAL}")


# MOVER LA SERPIENTE:
def move_snake(snake, direction, last_direction):
    """Dado a una lista de tuplas y una dirección, se añade una nueva coordenada al principio de la lista
    y se elimina el último, dando la sensación de movimiento.
    
    VARIABLES
        snake: Lista de tuplas con las coordenadas de la serpiente
        direction: La dirección a la que se va a mover: ('U', 'D', 'L', 'R')
        last_direction: La dirección anterior"""
    # OBTENER LAS COORDENADAS DE LA CABEZA Y LA COLA.
    head = snake[0]
    tail = snake.pop()

    # SUMARLE O RESTARLE 1 DEPENDIENDO DE LA DIRECCIÓN
    movement = { "U": (-1, 0), "D": (1, 0), "L": (0, -1), "R": (0, 1) }
    head = head[0] + movement[direction][0], head[1] + movement[direction][1]

    # AÑADE LA NUEVA CABEZA AL PRINCIPIO DE LA LISTA
    snake.insert(0, head)

    # PINTAR LA NUEVA CABEZA DEPENDIENDO DEL MOVIMIENTO.
    character = SNAKE_HORIZONTAL if direction in ['L', 'R'] else SNAKE_VERTICAL
    move_and_draw_char(head, f"{C_G}{character}")

    # COMPROBAR SI HA GIRADO Y MOSTRAR UN CARÁCTER DISTINTO EN LOS GIROS DEL CUERPO.
    if is_turning(direction, last_direction):
        move_and_draw_char(snake[1], f"{C_G}{SNAKE_TURN}")

    # BORRAR LA COLA PINTANDO UN ESPACIO EN BLANCO
    move_and_draw_char(tail, " ")

    # DEVUELVE LA POSICIÓN DE LA COLA ELIMINADA PARA USARLA LUEGO:
    return tail


def is_turning(direction, last_direction):
    """
    Devuelve si el movimiento actual implica un giro
    """
    # DIRECCIONES VERTICAL Y HORIZONTAL
    vertical = ['U', 'D']
    horizontal = ['L', 'R']

    # SI SE HA GIRADO EL EJE ACTUAL CAMBIA CON RESPECTO AL ANTERIOR
    if direction in vertical and last_direction in horizontal:
        return True
    elif direction in horizontal and last_direction in vertical:
        return True
    
    # NO SE HA GIRADO
    return False


def change_head_color(snake, direction, color, reset_color):
    # OBTENER LA CABEZA Y CAMBIAR DE COLOR
    head = snake[0]
    character = SNAKE_HORIZONTAL if direction in ['L', 'R'] else SNAKE_VERTICAL
    move_and_draw_char(head, f"{color}{character}{S_R}")
    
    # VOLVER A RESETEAR EL COLOR SI SE PIDE
    if reset_color:
        time.sleep(EAT_WAIT_TIME)
        move_and_draw_char(head, f"{C_G}{character}{S_R}")


# --------------------------------------------------------------------------
# SI EL JUGADOR SE HA CHOCADO
def check_collision(snake, map_limits):
    """
    Devuelve TRUE si se ha chocado con sigo misma o ha sobrepasado los límites del mapa. FALSE en caso contrario.
    """
    # GUARDAR LA POSICIÓN DE LA CABEZA
    head = snake[0]

    # COMPROBAR SI LA CABEZA COINCIDE CON ALGUNA DE LAS COORDENADAS DE SU CUERPO, O SI NO ESTÁ DENTRO DE LOS LÍMITES DEL MAPA.
    if head in snake[1:] or not in_limits(head, map_limits):
        return True

    # NO HA CHOCADO CON NADA
    return False


def in_limits(head, map_limits):
    # SI LA POSICIÓN VERTICAL DE LA CABEZA ESTÁ FUERA DE LOS LÍMITES DEL MAPA:
    if not map_limits['D'] > head[0] > map_limits['U']:
        return False
    # SI LA POSICIÓN HORIZONTAL DE LA CABEZA ESTÁ FUERA DE LOS LÍMITES DEL MAPA:
    elif not map_limits['L'] < head[1] < map_limits['R']:
        return False
    
    # ESTÁ DENTRO DE LOS LÍMITES
    return True


# --------------------------------------------------------------------------
def draw_fruit(snake, map_limits):
    """
    Pinta una fruta en la pantalla en una coordenada aleatoria dentro de los límites del mapa y fuera del cuerpo de la serpiente
    """
    # GUARDAR EL RANGO HORIZONTAL Y VERTICAL DEL MAPA:
    lines = list(range(map_limits['U'] + 1, map_limits['D']))
    columns = list(range(map_limits['L'] + 1, map_limits['R']))

    # GENERAR EL RANGO DE POSICIONES DONDE PUEDE CREARSE UNA FRUTA
    map_range = get_valid_range(snake, lines, columns)

    # MOVER EL CURSOR A UNA POSICIÓN ALEATORIA DENTRO DE MAP_RANGE Y PINTAR LA FRUTA.
    fruit_position = (random.choice(map_range))
    color = get_random_color()
    move_and_draw_char(fruit_position, f"{color}⬤{S_R}")

    # DEVOLVER LA POSICIÓN DE LA FRUTA CREADA:
    return fruit_position


def get_valid_range(snake, lines, columns):
    """
    Devuelve una lista con las posiciones posibles dentro de los límites del mapa y fuera del cuerpo de la serpiente
    """
    map_range = []
    for line in lines:
        for column in columns:
            coordenada = tuple([line, column])
            # FILTRAR LAS POSICIONES DONDE SE UBIQUE EL CUERPO DE LA SERPIENTE
            if coordenada not in snake:
                map_range.append(coordenada)
    return map_range


def get_random_color():
    """
    Devuelve un color aleatorio
    """
    colors = [C_G, C_LG, C_R, C_Y, C_LR, C_B, C_M, C_C, C_GRAY]
    return random.choice(colors)

# --------------------------------------------------------------------------
def check_eat(snake, tail, fruit):
    """
    Comprueba si las coordenadas de la cabeza de la serpiente coinciden con las de la fruta.
    """
    head = snake[0]

    # SI LAS COORDENADAS DE LA CABEZA COINCIDEN CON LAS DE LA FRUTA
    if head == fruit:
        # AÑADIMOS LA COLA A LA SERPIENTE Y LA PINTAMOS
        snake.append(tail)
        move_and_draw_char(tail, f"{C_G}■{S_R}")
        return True
    
    return False


# --------------------------------------------------------------------------
def show_game_info(username):
    """
    Esta funcion imprime el Score, la velocidad del juego, y el nombre de usuario debajo del mapa
    """
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
def obtain_frame_rate(action):
    if action in ['U', 'D']:
        # HACER QUE SE REDUZCA UN POCO LA VELOCIDAD AL IR EN DIRECCIÓN VERTICAL
        return 0.5 / speed
    return 0.3 / speed


# --------------------------------------------------------------------------
def end_game(died):
    if died:
        # SI EL JUGADOR MUERE, CARGA EN UN FICHERO EL HISTÓRICO DE LOS SCORES GUARDADOS POR CADA JUGADOR
        registro = save_scores(all_scores)
        time.sleep(1)

        # MOSTRAR LAS PUNTUACIONES
        show_scores(registro, C_M)
    else:
        # MOSTRAR UN AGRADECIMIENTO SI SE HA SALIDO DEL JUEGO POR EL BOTÓN Q
        show_thanks_text()

    # ANTES DE SALIR DEL JUEGO RESTAURAR TECLADO:
    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    move_cursor(lines + 6, 0)
    print(CURSOR_SHOW, end="")
    sys.exit(1)


def show_thanks_text():
    # LIMPIAR LA PANTALLA
    print(CLEAR_SCREEN)
    draw_map()

    # IMPRIMIR TEXTO
    move_cursor((lines // 2) + 5, 2)
    print(f"{f'THANKS FOR PLAYING!':^{columns}}")


# --------------------------------------------------------------------------
def save_scores(all_scores):
    # GUARDAR EL NUEVO REGISTRO EN LA LISTA DE SCORES
    registro = tuple((time.time(), nickname, score))
    all_scores.append(registro)

    # GUARDA EN EL FICHERO scores.pkl LA LISTA DE SCORES
    with open('scores.pkl', 'wb') as file:
        pickle.dump(all_scores, file)

    # DEVOLVER EL REGISTRO ACTUAL
    return registro


def load_scores():
    # CARGA EL FICHERO scores.pkl (SI EXISTE)
    try:
        with open('scores.pkl', 'rb') as file:
            return pickle.load(file)
    # SI NO EXISTE EL FICHERO, LA LISTA DE SCORES SE QUEDA VACÍA
    except FileNotFoundError:
        return []


# --------------------------------------------------------------------------
def show_scores(registro_actual, color_registro):
    # LIMPIAR LA PANTALLA
    print(CLEAR_SCREEN)
    draw_map()

    # IMPRIMIR GAME OVER
    move_cursor(7, 2)
    print(f"{C_R}{f'💀 GAME OVER 💀':^{columns - 2}}{S_R}")

    # ORDENAR DE MAYOR PUNTUACIÓN A MENOR PUNTUACIÓN LOS 10 MEJORES
    current_line = 7
    ranking = sorted(all_scores, key=lambda score: score[2], reverse=True)
    for element in ranking[:SCORE_MAX_LENGTH]:
        # RESALTAR EN COLOR DISTINTO LA PARTIDA ACTUAL, SI COINCIDE LA FECHA DEL REGISTRO CON LA FECHA DEL ACTUAL
        color = color_registro if element[0] == registro_actual[0] else S_R
        
        # IMPRIMIR REGISTRO
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
