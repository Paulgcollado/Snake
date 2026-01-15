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
import sys, tty, termios, threading, time, random, pickle, os
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional
from enum import Enum


# ==========================================================================
# CONSTANTES
#
# Datos y métodos constantes que se usan en todo el programa.
class Style:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    @staticmethod
    def move_cursor(line: int, column: int) -> str:
        """Mueve el cursor a la posición especificada"""
        return f"\033[{line};{column}H"

    @staticmethod
    def move_and_print(position: Tuple[int, int], text: str) -> None:
        """Mueve el cursor e imprime texto"""
        print(Style.move_cursor(*position), end="")
        print(text, end="", flush=True)


class Color:
    """Códigos para escribir en un color en la terminal"""
    GREEN = "\033[32m"
    LIGHT_GREEN = "\033[92m"
    RED = "\033[31m"
    YELLOW = "\033[33m"
    LIGHT_RED="\033[91m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    GRAY = "\033[37m"

    @staticmethod
    def random() -> str:
        """Devuelve un color aleatorio de la paleta de colores"""
        colors = [Color.GREEN, Color.LIGHT_GREEN, Color.RED, Color.YELLOW, Color.LIGHT_RED, Color.BLUE, Color.MAGENTA, Color.CYAN, Color.GRAY]
        return random.choice(colors)


class Terminal:
    """Constantes para el control de la terminal"""
    CURSOR_HIDE = "\033[?25l"
    CURSOR_SHOW = "\033[?25h"
    CLEAR_SCREEN = "\033c"
    REMOVE_LINE = "\033[2K"
    MOVE_UP = "\033[A"


class GameConfig:
    """Configuración del juego"""
    MAP_LINES = 15
    MAP_COLUMNS = 50
    INITIAL_POSITION = [(10, 10), (10, 9), (10, 8), (10, 7)]
    MIN_SPEED = 1
    MAX_SPEED = 15
    BASE_FRAME_RATE = 0.05
    EAT_WAIT_TIME = 0.15
    USERNAME_MAX_LENGTH = 15
    SCORE_MAX_LENGTH = 10
    SNAKE_VERTICAL = "█"
    SNAKE_HORIZONTAL = "■"
    SNAKE_TURN = "▮"


class Direction(Enum):
    """Direcciones posibles"""
    UP = "U"
    DOWN = "D"
    LEFT = "L"
    RIGHT = "R"

    @property
    def opposite(self):
        """Devuelve la dirección opuesta"""
        opposites = {
            Direction.UP: Direction.DOWN,
            Direction.DOWN: Direction.UP,
            Direction.LEFT: Direction.RIGHT,
            Direction.RIGHT: Direction.LEFT
        }
        return opposites[self]
    
    @property
    def movement(self) -> Tuple[int, int]:
        """Devuelve el vector de movimiento"""
        movements = { Direction.UP: (-1, 0), Direction.DOWN: (1, 0), Direction.LEFT: (0, -1), Direction.RIGHT: (0, 1) }
        return movements[self]
    
    @property
    def is_vertical(self) -> bool:
        """Verifica si la dirección es vertical"""
        return self in (Direction.UP, Direction.DOWN)
    
    @property
    def is_horizontal(self) -> bool:
        """Verifica si la dirección es horizontal"""
        return self in (Direction.LEFT, Direction.RIGHT)
        

# ==========================================================================
# CLASES
#
# Clases propias para el manejo del juego.
@dataclass
class MapLimits:
    """Límites del mapa del juego"""
    top: int
    bottom: int
    left: int
    right: int

    def contains(self, position: Tuple[int, int]) -> bool:
        """Verifica si una posición está dentro de los límites del mapa"""
        line, column = position
        in_vertical_range = self.top < line < self.bottom
        in_horizontal_range = self.left < column < self.right
        return in_vertical_range and in_horizontal_range


class GameMap:
    """Representa el mapa del juego"""

    def __init__(self, lines: int, columns: int):
        self.lines = lines
        self.columns = columns
        self.banner = """  ╔═╗╦ ╦╔╦╗╦ ╦╔═╗╔╗╔  ╔═╗╔╗╔╔═╗╦╔═╔═╗
  ╠═╝╚╦╝ ║ ╠═╣║ ║║║║  ╚═╗║║║╠═╣╠╩╗╠╣ 
  ╩   ╩  ╩ ╩ ╩╚═╝╝╚╝  ╚═╝╝╚╝╩ ╩╩ ╩╚═╝"""

    def draw(self) -> MapLimits:
        """Dibuja el mapa y devuelve sus límites"""
        print(Terminal.CLEAR_SCREEN, end="")
        print(f"{self.banner}     {Color.GRAY}DAW 2026{Style.RESET}")

        # DIBUJAR BORDES DEL MAPA
        print(f"▄"*(self.columns+2))
        print(f"█{' '*(self.columns)}█\n"*self.lines, end="")
        print(f"▀"*(self.columns+2))

        # DEVOLVER LOS LÍMITES DEL MAPA.
        return MapLimits(top = 4, bottom = self.lines + 5, left = 1, right = self.columns + 2)
    
    def show_game_info(self, username: str, score: int, speed: int) -> None:
        """Muestra la información del juego debajo del mapa"""
        width = self.columns // 3
        speed_text = speed if speed > 0 else f"{Color.RED}PAUSE{Style.RESET}"

        # IMPRIMIR CADA UNO, Y ALINEARLO A LA ANCHURA A LA IZQUIERDA, CENTRO Y DERECHA
        Style.move_and_print((self.lines + 6, 0), " " * self.columns)
        Style.move_and_print((self.lines + 6, 0),
            f" {f'🐍 SCORE: {score}':<{width}}"
            f"{f'🚀 SPEED: {speed_text}':^{width}}"
            f"{f'🤖 {username}':>{width}}"
        )
    

class Snake:
    """Representa la serpiente del juego"""

    def __init__(self, initial_position: List[Tuple[int, int]]):
        self.position = initial_position[:]
        self.direction = Direction.RIGHT
        self.speed = 5
        self.growth_pending = 0
    
    @property
    def head(self) -> Tuple[int, int]:
        """Devuelve la posición de la cabeza"""
        return self.position[0]
    
    @property
    def tail(self) -> Tuple[int, int]:
        """Devuelve la posición de la cola"""
        return self.position[-1]

    def draw(self) -> None:
        """Dibuja la serpiente completa"""
        for position in self.position:
            Style.move_and_print(position, f"{Color.GREEN}{GameConfig.SNAKE_HORIZONTAL}{Style.RESET}")
    
    def move(self, new_direction: Direction, last_direction: Direction) -> Tuple[int, int]:
        """Mueve la serpiente en una dirección y devuelve la posición de la cola eliminada"""
        # VALIDAR DIRECCIÓN.
        if new_direction.opposite == self.direction:
            new_direction = self.direction
        self.direction = new_direction

        # CALCULAR LA NUEVA POSICIÓN DE LA CABEZA.
        line, column = self.head
        horizontal_direction, vertical_direction = new_direction.movement
        new_head = (line + horizontal_direction, column + vertical_direction)

        # AÑADIR LA NUEVA CABEZA
        self.position.insert(0, new_head)
        head_character = GameConfig.SNAKE_HORIZONTAL if new_direction.is_horizontal else GameConfig.SNAKE_VERTICAL
        Style.move_and_print(new_head, f"{Color.GREEN}{head_character}{Style.RESET}")

        # COMPROBAR SI HA GIRADO Y MOSTRAR UN CARÁCTER DISTINTO EN LOS GIROS DEL CUERPO.
        if self._is_turning(self.direction, last_direction):
            Style.move_and_print(self.position[1], f"{Color.GREEN}{GameConfig.SNAKE_TURN}{Style.RESET}")

        if self.growth_pending > 0:
            self.growth_pending -= 1
            return None
        tail = self.position.pop()
        Style.move_and_print(tail, " ")
        return tail
    
    def grow(self) -> None:
        """Marca la serpiente para crecer en el próximo movimiento"""
        self.growth_pending += 1
    
    def check_collision(self, map_limits: MapLimits) -> bool:
        """Verifica colisiones con bordes o con sí misma"""
        # Colisión con bordes
        if not map_limits.contains(self.head):
            return True
        
        # Colisión consigo misma
        return self.head in self.position[1:-1]
    
    def change_head_color(self, color: str, reset: bool = True) -> None:
        """Cambia temporalmente el color de la cabeza"""
        head_character = GameConfig.SNAKE_HORIZONTAL if self.direction.is_horizontal else GameConfig.SNAKE_VERTICAL
        Style.move_and_print(self.head, f"{color}{head_character}{Style.RESET}")
        if reset:
            time.sleep(GameConfig.EAT_WAIT_TIME)
            Style.move_and_print(self.head, f"{Color.GREEN}{head_character}{Style.RESET}")

    def adjust_speed(self, change: int) -> None:
        """Ajusta la velocidad de la serpiente"""
        new_speed = self.speed + change
        if GameConfig.MIN_SPEED <= new_speed <= GameConfig.MAX_SPEED:
            self.speed = new_speed
    
    def set_speed(self, speed: int) -> None:
        """Establece la velocidad de la serpiente"""
        if speed == 0:
            self.speed = speed
            return
        self.speed = max(GameConfig.MIN_SPEED, min(speed, GameConfig.MAX_SPEED))

    def _is_turning(self, direction: Direction, last_direction = Direction) -> bool:
        """Comprueba si se ha realizado un giro en la dirección de la serpiente"""
        if direction.is_vertical and last_direction.is_horizontal:
            return True
        elif direction.is_horizontal and last_direction.is_vertical:
            return True
        return False


class Fruit:
    """Representa la fruta que come la serpiente"""

    def __init__(self, snake: Snake, map_limits: MapLimits):
        self.position = self._generate_position(snake, map_limits)
        self.color = Color.random()
        self.draw()

    def draw(self) -> None:
        """Dibuja la fruta en la pantalla"""
        Style.move_and_print(self.position, f"{self.color}⬤{Style.RESET}")

    def __get_valid_range(self, snake, lines, columns):
        map_range = []
        for line in lines:
            for column in columns:
                coordenada = tuple([line, column])
                if coordenada not in snake.position:
                    map_range.append(coordenada)
        return map_range

    def _generate_position(self, snake: Snake, map_limits: MapLimits) -> Tuple[int, int]:
        """Genera una posición aleatoria para la fruta"""
        map_range = []
        for line in range(map_limits.top + 1, map_limits.bottom):
            for column in range(map_limits.left + 1, map_limits.right):
                position = tuple([line, column])
                if position not in snake.position:
                    map_range.append(position)

        # SI NO HAY POSICIONES DISPONIBLES
        if not map_range:
            return (map_limits.top + 1, map_limits.left + 1)
        return random.choice(map_range)
    
    def is_eaten(self, snake: Snake) -> bool:
        """Verifica si la serpiente ha comido una fruta"""
        return snake.head == self.position


class ScoreManager:
    """Maneja el sistema de puntuaciones"""

    def __init__(self):
        self.scores: List[Tuple[float, str, int]] = []
        self.load_scores()
        pass

    def add_score(self, username: str, score: int) -> Tuple[float, str, int]:
        """Añade una nueva puntuación"""
        record = tuple((time.time(), username, score))
        self.scores.append(record)
        self.save_scores()
        return record
    
    def save_scores(self) -> None:
        """Guarda en el fichero scores.pkl la lista de scores"""
        try:
            with open('scores.pkl', 'wb') as file:
                pickle.dump(self.scores, file)
        except Exception as e:
            print(f"Error guardando puntuaciones: {e}")
    
    def load_scores(self) -> None:
        """Carga las puntuaciones desde un fichero"""
        try:
            with open('scores.pkl', 'rb') as file:
                self.scores = pickle.load(file)
        except FileNotFoundError:
            self.scores = []
        except Exception as e:
            print(f"Error cargando puntuaciones: {e}")
            self.scores = []
    
    def get_ranking(self, limit: int = 10) -> List[Tuple[float, str, int]]:
        """Obtiene el ranking de mejores puntuaciones"""
        return sorted(self.scores, key=lambda score: score[2], reverse=True)[:limit]


class InputHandler:
    """Maneja la entrada de teclado en segundo plano"""

    def __init__(self):
        self.fd = sys.stdin.fileno()
        self.old_settings = termios.tcgetattr(self.fd)
        self.lock = threading.Lock()
        self.current_key = "R"
        self.thread = None
    
    def start(self) -> None:
        """Inicia el hilo de lectura de teclado"""
        self.thread = threading.Thread(target=self._read_keyboard, daemon=True)
        self.thread.start()

    def _read_keyboard(self) -> None:
        """Lee las teclas presionadas en segundo plano"""
        try:
            tty.setcbreak(self.fd)
            while True:
                ch1 = sys.stdin.read(1)
                if ch1 == '\x1b':
                    ch2 = sys.stdin.read(1)
                    ch3 = sys.stdin.read(1)
                    key_seq = ch1 + ch2 + ch3
                    
                    key_map = {
                        '\x1b[A': "U",  # Flecha arriba
                        '\x1b[B': "D",  # Flecha abajo
                        '\x1b[C': "R",  # Flecha derecha
                        '\x1b[D': "L",  # Flecha izquierda
                    }
                    
                    with self.lock:
                        self.current_key = key_map.get(key_seq, self.current_key)
                
                elif ch1 in ['q', 'p', '+', '-']:
                    with self.lock:
                        self.current_key = ch1.upper() if ch1 != 'q' else 'Q'
                
                # Pequeña pausa para evitar uso excesivo de CPU
                time.sleep(0.01)
        except Exception:
            pass
        finally:
            self._restore_terminal()
    
    def get_key(self) -> str:
        """Obtiene la tecla actualmente presionada"""
        with self.lock:
            return self.current_key
    
    def stop(self) -> None:
        """Detiene el hilo de lectura y restaura el terminal"""
        self._restore_terminal()
    
    def _restore_terminal(self) -> None:
        """Restaura la configuración original del terminal"""
        termios.tcsetattr(self.fd, termios.TCSADRAIN, self.old_settings)


# ==========================================================================
# FUNCIONES
#
# Estas son todas las funciones que usa el programa
# --------------------------------------------------------------------------
def get_username(game_map: GameMap) -> str:
    """Solicita y valida el nombre de usuario"""
    while True:
        Style.move_and_print((game_map.lines + 6, 0), f" {Terminal.CURSOR_SHOW}{Style.BOLD}🤖 PLAYER NAME: {Style.RESET}{Color.GRAY}")
        username = input()
        if len(username) < GameConfig.USERNAME_MAX_LENGTH:
            return username
        
        # NOMBRE DEMASIADO LARGO
        print(f"{Terminal.CURSOR_HIDE}{Color.RED}Username must be less than 15 characters{Style.RESET}")
        time.sleep(1)


def calculate_frame_rate(direction: Direction, speed: int) -> float:
    """Calcula el tiempo de espera entre frames"""
    base_rate = 0.5 if direction.is_vertical else 0.3
    return base_rate / max(1, speed)


def show_game_over(game_map: GameMap, score_manager: ScoreManager, current_record: Tuple[float, str, int]) -> None:
    """Muestra la pantalla de fin de juego con las puntuaciones"""
    game_map.draw()
    Style.move_and_print((6, 2), f"{Color.RED}{Style.BOLD}{f'💀 GAME OVER 💀':^{game_map.columns - 2}}{Style.RESET}")
    Style.move_and_print((7, 2), f"{'―――――――――――――――――――――――――――――――':^{game_map.columns - 1}}")
    
    # MOSTRAR EL RANKING
    ranking = score_manager.get_ranking(GameConfig.SCORE_MAX_LENGTH)
    for i, record in enumerate(ranking, start=8):
        timestamp, username, score = record
        color = f"{Style.BOLD}{Color.MAGENTA}" if timestamp == current_record[0] else Style.RESET
        item = f"{f'🤖 {username}':<15}{score:>15}"
        Style.move_and_print((i, 2), f"{color}{item:^{game_map.columns - 2}}{Style.RESET}")


# --------------------------------------------------------------------------
# COMENZAR EL JUEGO
def main_game_loop() -> None:
    """Bucle principal del juego"""
    input_handler = InputHandler()
    game_map = GameMap(GameConfig.MAP_LINES, GameConfig.MAP_COLUMNS)
    score_manager = ScoreManager()
    
    try:
        map_limits = game_map.draw()
        username = get_username(game_map)
        
        # INICIALIZAR EL JUEGO
        snake = Snake(GameConfig.INITIAL_POSITION)
        fruit = Fruit(snake, map_limits)
        current_score = 0
        snake.draw()
        game_map.show_game_info(username, current_score, snake.speed)
        
        # INICIAR LA LECTURA DE TECLADO
        input_handler.start()
        print(Terminal.CURSOR_HIDE, end="")
        
        # VARIABLES DE ESTADO
        is_paused = False
        last_speed = snake.speed
        last_direction = Direction.RIGHT
        
        # BUCLE PRINCIPAL
        while True:
            # OBTNER LA TECLA DE DIRECCIÓN
            key = input_handler.get_key()
            
            # MANEJAR PAUSA
            if is_paused:
                if key == 'P':
                    is_paused = False
                    snake.set_speed(last_speed)
                    game_map.show_game_info(username, current_score, snake.speed)
                continue
            
            # MANEJAR CONTROLES PRINCIPALES
            if key == 'Q':
                break
            elif key == 'P':
                is_paused = True
                last_speed = snake.speed
                snake.set_speed(0)
                game_map.show_game_info(username, current_score, snake.speed)
                continue
            elif key in ['+', '-']:
                snake.adjust_speed(1 if key == '+' else -1)
                game_map.show_game_info(username, current_score, snake.speed)
                input_handler.current_key = last_direction
                continue
            
            # CONVERTIR TECLA A DIRECCIÓN
            try:
                direction = Direction(key)
            except ValueError:
                direction = last_direction
            
            # MOVER SERPIENTE
            removed_tail = snake.move(direction, last_direction)
            
            # COMPROBAR SI SE HA COMIDO UNA FRUTA
            if fruit.is_eaten(snake):
                snake.grow()
                if removed_tail:
                    snake.position.append(removed_tail)
                    Style.move_and_print(removed_tail, f"{Color.GREEN}■{Style.RESET}")
                
                snake.change_head_color(fruit.color, reset=True)
                fruit = Fruit(snake, map_limits)
                current_score += 1
                game_map.show_game_info(username, current_score, snake.speed)
            
            # COMPROBAR COLISIONES
            if snake.check_collision(map_limits):
                snake.change_head_color(Color.RED, reset=False)
                current_record = score_manager.add_score(username, current_score)
                time.sleep(1)
                show_game_over(game_map, score_manager, current_record)
                break
            
            # ACTUALIZAR ESTADO
            last_direction = direction
            
            # CONTROL DE VELOCIDAD
            frame_delay = calculate_frame_rate(direction, snake.speed)
            time.sleep(frame_delay)
    except KeyboardInterrupt:
        pass
    finally:
        # LIMPIEZA DE LA TERMINAL
        print(Terminal.CURSOR_SHOW + Style.RESET)
        print(Style.move_cursor(GameConfig.MAP_LINES + 5, 0))
        input_handler.stop()
        

# ==========================================================================
# PUNTO DE ENTRADA
if __name__ == "__main__":
    main_game_loop()