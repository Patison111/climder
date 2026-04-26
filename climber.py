import customtkinter as ctk
import pygame
from pygame.locals import *
from random import randint
from PIL import Image
import os

#налаштування теми меню
ctk.set_appearance_mode("dark")       #темна тема customtkinter

#глобальні змінні
player_name  = None   #ім'я гравця, введене в меню
game_started = False  #чи натиснув гравець СТАРТ

current_path  = os.path.dirname(os.path.realpath(__file__))  #папка з цим файлом
button_size   = (500, 100)   #ширина × висота кнопок
window_width  = 1920
window_height = 1080

#розмір ігрового вікна
WIN_W = 1366   # ширина ігрового вікна
WIN_H = 768    # висота ігрового вікна

#1 метр = 10 пікселів
PIXELS_PER_METER = 90

#земля знаходиться на world_y = 0, усе що вище — від'ємні значення Y
GROUND_WORLD_Y = 0          #Y-координата верхнього краю землі
GROUND_H       = 80         #висота зеленої смужки землі
GROUND_COLOR   = (60, 120, 40)   #темно-зелений
GROUND_BORDER  = (40, 90, 25)    #ще темніший зелений для лінії

#кожен кадр швидкість падіння збільшується на GRAVITY
GRAVITY = 0.6   #прискорення вільного падіння (пікселі / кадр²)

MAX_STAMINA   = 300   #максимальна витривалість
STAMINA_DRAIN = 1     #скільки витривалості витрачається за 1 кадр
STAMINA_REGEN = 1     #скільки відновлюється за 1 кадр

SEGMENT_H    = 120   #висота одного поверху гори
MIN_W        = 300   #мінімальна ширина гори
MAX_W        = 700   #максимальна ширина гори
MAX_SEGMENTS = 120   #скільки сегментів зберігаємо одночасно (старі видаляються)

PLATFORM_W      = 180   #ширина платформи
PLATFORM_H      = 18    #товщина платформи
PLATFORM_COLOR  = (180, 130, 60)   #коричнево-жовтий
PLATFORM_BORDER = (220, 170, 80)   #золотиста рамка платформи

PLATFORM_CHANCE = 0.18  #ймовірність (0–1) що на сегменті з'явиться платформа

# ──────────────────────────────────────────
#  ХМАРИ
# ──────────────────────────────────────────

class Cloud:
    """Одна хмара що повільно пливе праворуч і повторює цикл."""

    def __init__(self, x: float, world_y: int, scale: float, speed: float):
        self.x       = x          # позиція у пікселях екрану (горизонталь)
        self.world_y = world_y    # прив'язана до світу по вертикалі
        self.scale   = scale      # масштаб: 0.5–1.5
        self.speed   = speed      # пікселів за кадр

        # форма хмари: список кіл (dx, dy, r) відносно центру
        self.circles = self._make_shape()

    def _make_shape(self):
        """Генерує унікальну форму хмари з 4–6 кіл."""
        n   = randint(4, 6)
        cir = []
        x   = 0
        for i in range(n):
            r  = int((randint(22, 42)) * self.scale)
            dy = randint(-10, 10)
            cir.append((x, dy, r))
            x += int(r * 1.2)
        return cir

    def update(self):
        self.x += self.speed
        # якщо хмара виплила за правий край — повертаємо ліворуч
        max_x = max(cx for cx, _, r in self.circles) + WIN_W
        if self.x - 200 > WIN_W:
            self.x = -max_x

    def draw(self, surface: pygame.Surface, camera_y: int):
        sy = self.world_y - camera_y  # позиція на екрані по вертикалі
        # малюємо лише якщо видима
        if sy < -200 or sy > WIN_H + 200:
            return
        for dx, dy, r in self.circles:
            cx = int(self.x + dx)
            cy = int(sy + dy)
            # тінь (трохи темніша, зміщена вниз-праворуч)
            pygame.draw.circle(surface, (180, 200, 220), (cx + 4, cy + 6), r)
            # основне тіло хмари
            pygame.draw.circle(surface, (230, 240, 255), (cx, cy), r)
            # блик зверху
            pygame.draw.circle(surface, (255, 255, 255), (cx - r // 5, cy - r // 4), max(4, r // 3))


def create_clouds(count: int = 18) -> list:
    """Генерує початковий набір хмар розміщених по всій висоті початкового виду."""
    clouds = []
    for _ in range(count):
        x       = randint(-300, WIN_W + 100)
        world_y = randint(-(WIN_H * 20), -40)   # хмари від землі до великої висоти
        scale   = round(0.5 + randint(0, 100) / 100.0, 2)
        speed   = round(0.15 + randint(0, 60) / 100.0, 2)
        clouds.append(Cloud(float(x), world_y, scale, speed))
    return clouds


def extend_clouds(clouds: list, camera_y: int):
    """Якщо камера підіймається вище найвищої хмари — додаємо нові."""
    highest = min(c.world_y for c in clouds) if clouds else 0
    while highest > camera_y - WIN_H * 3:
        x       = randint(-300, WIN_W + 100)
        world_y = highest - randint(120, 400)
        scale   = round(0.5 + randint(0, 100) / 100.0, 2)
        speed   = round(0.15 + randint(0, 60) / 100.0, 2)
        clouds.append(Cloud(float(x), world_y, scale, speed))
        highest = world_y

#МЕНЮ

def show_menu():
    #відображає головне меню перед запуском гри. гравець вводить ім'я і натискає СТАРТ
    #після закриття меню глобальні змінні player_name і game_started оновлюються

    global player_name, game_started

    #створюємо головне вікно
    app = ctk.CTk()
    app.title("Меню")

    #центруємо вікно на екрані
    sw = app.winfo_screenwidth()
    sh = app.winfo_screenheight()
    app.geometry(f"{window_width}x{window_height}+{(sw - window_width) // 2}+{(sh - window_height) // 2}")
    app.overrideredirect(True)    #прибираємо рамку операційної системи
    app.attributes('-topmost', True)  #вікно поверх усіх інших

    #шрифти
    font_big = ctk.CTkFont(family="Pixelify Sans", size=48)
    font_mid = ctk.CTkFont(family="Pixelify Sans", size=16)

    #запускаєм музику
    try:
        pygame.mixer.init()
        pygame.mixer.music.load('main_menu_dark.mp3')
        pygame.mixer.music.play(-1)   # -1 = нескінченний повтор
    except:
        pass   #якщо файл не знайдено то пропускаємо

    #намагаємося завантажити фонове зображення меню
    try:
        ip = os.path.join(current_path, "menu.png")
        mi = ctk.CTkImage(light_image=Image.open(ip), dark_image=Image.open(ip),
                          size=(window_width, window_height))
        ctk.CTkLabel(app, text="", image=mi).place(x=0, y=0, relwidth=1, relheight=1)
    except:
        pass

    def start():
        #обробник кнопки СТАРТ: перевіряє ім'я і запускає гру
        global player_name, game_started
        name = entry.get()
        if name and len(name) <= 6:
            player_name  = name
            game_started = True
            try:
                pygame.mixer.music.stop()
            except:
                pass
            app.destroy()   #закриваємо меню → переходимо до ігрового циклу
        elif len(name) > 6:
            error_label.configure(text="Макс. 6 символів!")
        else:
            error_label.configure(text="Введіть ім'я!")

    def exit_app():
        #закриває програму
        global game_started
        game_started = False
        try:
            pygame.mixer.music.stop()
        except:
            pass
        app.destroy()

    #позиціонування елементів: лівий відступ lx, вертикальний центр cy
    lx, cy = 80, window_height // 2

    ctk.CTkLabel(app, text="CLIMBER", font=font_big,
                 fg_color="transparent", text_color="white").place(x=lx, y=cy - 280)

    entry = ctk.CTkEntry(app, width=300, height=40,
                         placeholder_text="Введіть ім'я (макс. 6 символів)", font=font_mid)
    entry.place(x=lx, y=cy - 180)

    #мітка для відображення помилок
    error_label = ctk.CTkLabel(app, text="", text_color="red",
                               font=font_mid, fg_color="transparent")
    error_label.place(x=lx, y=cy - 120)

    #кнопки СТАРТ і ВИХІД
    for path, cmd, yo in [("start_button.png", start, cy - 60),
                          ("exit_button.png",  exit_app, cy + 60)]:
        try:
            fp  = os.path.join(current_path, path)
            img = ctk.CTkImage(light_image=Image.open(fp), dark_image=Image.open(fp),
                               size=button_size)
            btn = ctk.CTkButton(app, text="", image=img, width=button_size[0],
                                height=button_size[1], fg_color="transparent",
                                hover_color="#333333", corner_radius=0, command=cmd)
        except:
            #звичайна текстова кнопка якщо не виходе перше
            btn = ctk.CTkButton(app, text="СТАРТ" if cmd == start else "ВИХІД",
                                font=font_big, width=300, height=80, command=cmd)
        btn.place(x=lx, y=yo)

    app.mainloop()   #запускаємо цикл

# ──────────────────────────────────────────
#  МЕНЮ ПАУЗИ  (pygame-оверлей)
# ──────────────────────────────────────────

# Константи вигляду паузи
PAUSE_BG_COLOR    = (10, 15, 30, 200)   # RGBA темний напівпрозорий оверлей
PAUSE_PANEL_COLOR = (20, 28, 50)        # фон панелі
PAUSE_BORDER      = (80, 120, 200)      # синя рамка
PAUSE_BTN_NORMAL  = (35, 50, 90)        # кнопка звичайна
PAUSE_BTN_HOVER   = (60, 90, 160)       # кнопка при наведенні
PAUSE_BTN_TEXT    = (200, 220, 255)
PAUSE_TITLE_TEXT  = (180, 210, 255)


class PauseButton:
    """Одна кнопка меню паузи."""

    def __init__(self, label: str, x: int, y: int, w: int, h: int):
        self.label = label
        self.rect  = pygame.Rect(x, y, w, h)

    def draw(self, surface: pygame.Surface, font, mouse_pos):
        hovered = self.rect.collidepoint(mouse_pos)
        color   = PAUSE_BTN_HOVER if hovered else PAUSE_BTN_NORMAL
        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        pygame.draw.rect(surface, PAUSE_BORDER, self.rect, 2, border_radius=8)
        txt = font.render(self.label, True, PAUSE_BTN_TEXT)
        surface.blit(txt, (self.rect.centerx - txt.get_width() // 2,
                            self.rect.centery - txt.get_height() // 2))

    def is_clicked(self, pos) -> bool:
        return self.rect.collidepoint(pos)


def draw_pause_menu(surface: pygame.Surface, font_big, font_mid, mouse_pos,
                    btn_continue: PauseButton, btn_restart: PauseButton,
                    btn_main_menu: PauseButton):
    """Малює напівпрозорий оверлей паузи поверх гри."""
    # напівпрозорий фон
    overlay = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
    overlay.fill(PAUSE_BG_COLOR)
    surface.blit(overlay, (0, 0))

    # панель
    pw, ph = 420, 340
    px, py = WIN_W // 2 - pw // 2, WIN_H // 2 - ph // 2
    panel  = pygame.Surface((pw, ph), pygame.SRCALPHA)
    panel.fill((*PAUSE_PANEL_COLOR, 230))
    surface.blit(panel, (px, py))
    pygame.draw.rect(surface, PAUSE_BORDER, (px, py, pw, ph), 3, border_radius=12)

    #заголовок ПАУЗА
    title = font_big.render("  ПАУЗА", True, PAUSE_TITLE_TEXT)
    surface.blit(title, (WIN_W // 2 - title.get_width() // 2, py + 28))

    # роздільник
    pygame.draw.line(surface, PAUSE_BORDER,
                     (px + 30, py + 90), (px + pw - 30, py + 90), 2)

    # кнопки
    btn_continue.draw(surface, font_mid, mouse_pos)
    btn_restart.draw(surface, font_mid, mouse_pos)
    btn_main_menu.draw(surface, font_mid, mouse_pos)

#КЛАС ПЛАТФОРМИ

class Platform:
    #горизонтальна дерев'яна платформа закріплена на горі. гравець може впасти на неї зверху

    def __init__(self, world_y: int, x: int):
        self.world_y = world_y   #Y верхнього краю платформи у світі
        self.x       = x         #X лівого краю платформи у світі
        self.w       = PLATFORM_W
        self.h       = PLATFORM_H

    @property #штука для зникнення дужок у функцій (типу не app.mainloop(), а app.mainloop )
    def rect_world(self) -> pygame.Rect:
        #повертає pygame.Rect у світових координатах (для колізій)
        return pygame.Rect(self.x, self.world_y, self.w, self.h)

    def draw(self, surface: pygame.Surface, camera_y: int):
        #малює платформу з урахуванням зсуву камери. camera_y — верхній край вікна перегляду у світових координатах
        #якщо платформа поза екраном то пропускаємо малювання

        sy = self.world_y - camera_y   #Y на екрані
        if sy > WIN_H + self.h or sy + self.h < 0:
            return   #платформа за межами екрану то не малюємо
        r = pygame.Rect(self.x, sy, self.w, self.h)
        pygame.draw.rect(surface, PLATFORM_COLOR, r)        #заливка
        pygame.draw.rect(surface, PLATFORM_BORDER, r, 3)    #рамка

#КЛАС СЕГМЕНТУ ГОРИ

#кольори для малювання сегментів гори
SEG_COLOR  = (85, 110, 140)    #основний синьо-сірий колір скелі
SEG_BORDER = (55, 78, 108)     #темніша рамка
SEG_ACCENT = (130, 165, 205)   #світліша лінія верхнього краю


class MountainSegment:
    #один поверх гори це прямокутний блок висотою SEGMENT_H
    #гора складається з багатьох таких сегментів розміщених один над одним
    #кожен сегмент може мати або не мати платформу всередині

    def __init__(self, world_top: int, seg_left: int, seg_right: int):
        self.world_top = world_top          #Y верхнього краю сегменту у світі
        self.left      = seg_left           #X лівої межі
        self.right     = seg_right          #X правої межі
        self.w         = seg_right - seg_left
        self.platform: Platform | None = None   #платформа (або None)

        #випадковим чином вирішуємо чи з'явиться платформа на цьому сегменті
        if randint(0, 99) < int(PLATFORM_CHANCE * 100):
            #розміщуємо платформу у випадковому місці всередині сегменту
            px = randint(seg_left, max(seg_left, seg_right - PLATFORM_W))
            py = world_top + randint(20, SEGMENT_H - 30)
            self.platform = Platform(py, px)

    def contains_x(self, x: int) -> bool:
        #перевіряє чи знаходиться X координата всередині ширини сегменту
        return self.left <= x <= self.right

    def draw(self, surface: pygame.Surface, camera_y: int):
        #малює сегмент (і платформу якщо є) з урахуванням камери
        st = self.world_top - camera_y   #Y верхнього краю на екрані
        #пропускаємо сегменти що повністю поза екраном
        if st > WIN_H + SEGMENT_H or st + SEGMENT_H < -SEGMENT_H:
            return
        r = pygame.Rect(self.left, st, self.w, SEGMENT_H)
        pygame.draw.rect(surface, SEG_COLOR, r)                           #тіло сегменту
        pygame.draw.line(surface, SEG_ACCENT, (self.left, st), (self.right, st), 4)  #блік зверху
        pygame.draw.rect(surface, SEG_BORDER, r, 2)                       #рамка
        if self.platform:
            self.platform.draw(surface, camera_y)   #малюємо платформу поверх

#КЛАС ГОРИ

class MountainWall:
    #зберігає список сегментів у порядку від найвищого до найнижчого
    #нові сегменти додаються знизу камери у міру підняття гравця
    #старі сегменти внизу видаляються щоб не перевантажувати

    def __init__(self):
        self.segments: list[MountainSegment] = []
        #починаємо генерацію прямо від рівня землі
        start_top = GROUND_WORLD_Y - SEGMENT_H
        self._gen_from(start_top, count=15)   #генеруємо 15 перших сегментів

    def _new_segment(self, world_top: int, prev_seg=None) -> MountainSegment:
        #створює новий сегмент враховуючи розмір та положення попереднього
        #ширина та положення сегменту трохи відрізняється від попереднього

        if prev_seg is None:
            #перший сегмент по центру екрану
            w    = randint(MIN_W, MAX_W)
            left = (WIN_W - w) // 2
        else:
            #наступні сегменти: незначно змінюємо ширину та зсуваємо ліворуч/праворуч
            w     = max(MIN_W, min(MAX_W, prev_seg.w + randint(-80, 80)))
            shift = randint(-120, 120)
            left  = prev_seg.left + shift
            left  = max(0, min(WIN_W - w, left))   #не виходимо за межі екрану
        return MountainSegment(world_top, left, left + w)

    def _gen_from(self, world_top: int, count: int):
        #генерує count нових сегментів вище world_top і додає їх у список
        y        = world_top
        new_segs = []
        for _ in range(count):
            #беремо попередній сегмент як базу для наступного
            prev = new_segs[-1] if new_segs else (self.segments[0] if self.segments else None)
            s    = self._new_segment(y, prev)
            new_segs.append(s)
            y -= SEGMENT_H   #кожен наступний сегмент вище на SEGMENT_H

        #нові сегменти йдуть на початок списку, старі в кінець
        self.segments = new_segs[::-1] + self.segments
        #обрізаємо список якщо він перевищує MAX_SEGMENTS
        if len(self.segments) > MAX_SEGMENTS:
            self.segments = self.segments[:MAX_SEGMENTS]

    @property
    def highest_top(self) -> int:
        #Y-координата найвищого сегменту
        return self.segments[0].world_top if self.segments else 0

    def extend_up(self, until_world_y: int):
        #добудовує гору вгору якщо камера наближається до верху існуючих сегментів
        if self.highest_top > until_world_y:
            need = (self.highest_top - until_world_y) // SEGMENT_H + 5
            self._gen_from(self.highest_top - SEGMENT_H, count=need)

    def segment_at(self, world_y: int) -> MountainSegment | None:
        #знаходить сегмент що містить задану world_y-координату
        #використовується для перевірки чи знаходиться гравець всередині гори

        for s in self.segments:
            if s.world_top <= world_y < s.world_top + SEGMENT_H:
                return s
        return None

    def all_platforms(self) -> list[Platform]:
        #повертає список усіх платформ на горі (для перевірки колізій)
        return [s.platform for s in self.segments if s.platform is not None]

    def draw(self, surface: pygame.Surface, camera_y: int):
        #малює всі сегменти
        for s in self.segments:
            s.draw(surface, camera_y)

#КЛАС ГРАВЦЯ

class Player:

    """
    Керування:
      A / D  — рух ліворуч / праворуч
      W / S  — лазіння вгору / вниз по горі (лише якщо торкається стіни)
      ESC    — пауза

    Фізика:
      якщо гравець НЕ тисне W/S на горі то він падає від гравітації
      на землі та платформах стоїть та відновлює витривалість
      якщо витривалість = 0 лазіння заблоковано, гравець падає
    """

    def __init__(self, world_x: int, world_y: int):
        #позиція у світових координатах
        self.world_x = float(world_x)
        self.world_y = float(world_y)
        self.vel_y   = 0.0   #вертикальна швидкість

        #розміри спрайту гравця
        self.width  = 70
        self.height = 100
        self.speed  = 7   #швидкість руху

        #стани контакту з поверхнями
        self.on_mountain = False   #чіпляється за гору (W/S натиснуті)
        self.on_ground   = False   #стоїть на землі
        self.on_platform = False   #стоїть на платформі

        #анімація
        self.direction   = "right"   #куди дивиться гравець
        self.action      = "idle"    #поточна дія: idle / walk / climb
        self.frame       = 0         #індекс поточного кадру анімації
        self.frame_timer = 0         #лічильник для зміни кадрів
        self.frame_delay = 10        #кожні N ігрових кадрів — наступний кадр анімації

        #витривалість
        self.stamina = float(MAX_STAMINA)

        #завантажуємо спрайти
        self.sprites = self._load_sprites()

    def _load_sprites(self):
        """завантажує PNG-спрайти з папки sprites/

        якщо файл не знайдено то підставляємо кольоровий прямокутник-заглушку
        """
        def try_load(name, color):
            """намагається завантажити спрайт або повертає кольоровий квадрат"""
            p = os.path.join(current_path, "sprites", name)
            if os.path.exists(p):
                img = pygame.image.load(p).convert_alpha()
                return pygame.transform.scale(img, (self.width, self.height))
            #однотонна поверхня потрібного розміру
            s = pygame.Surface((self.width, self.height))
            s.fill(color)
            return s

        #словник: ключ — назва стану, значення — список кадрів
        return {
            "idle_right": [try_load("idle_right.png", (0, 200, 80))],
            "idle_left":  [try_load("idle_left.png",  (0, 200, 80))],
            "walk_right": [try_load("walk_right_0.png", (0, 180, 100)),
                           try_load("walk_right_1.png", (0, 160, 120))],
            "walk_left":  [try_load("walk_left_0.png",  (0, 180, 100)),
                           try_load("walk_left_1.png",  (0, 160, 120))],
            "climb":      [try_load("climb_0.png", (0, 140, 160)),
                           try_load("climb_1.png", (0, 120, 180))],
            "fall":       [try_load("idle_right.png", (200, 80, 0))],  #помаранчева заглушка при падінні
        }

    def _sprite_key(self) -> str:
        """повертає ключ для вибору потрібного набору спрайтів залежно від стану"""
        if not self.on_mountain and not self.on_ground and not self.on_platform:
            return "fall"   #гравець у повітрі то анімація падіння
        if self.action == "climb":
            return "climb"
        if self.action == "walk":
            return f"walk_{self.direction}"
        return f"idle_{self.direction}"

    def update(self, keys, wall: MountainWall):
        """Порядок:
          1. Визначаємо чи торкається гравець гори (і чи тисне W/S)
          2. Перевіряємо землю та платформи
          3. Обробляємо горизонтальний рух
          4. Застосовуємо вертикальну фізику (лазіння або гравітацію)
          5. Оновлюємо витривалість
          6. Встановлюємо стан анімації
        """
        moving   = False   #чи рухається гравець горизонтально
        climbing = False   #чи лазить гравець

        #допоміжні точки тіла гравця для колізій
        mid_x  = int(self.world_x + self.width / 2)   #горизонтальний центр
        feet_y = int(self.world_y + self.height)       #нижній край

        #чи тисне гравець клавіші лазіння W або S
        pressing_climb = keys[pygame.K_w] or keys[pygame.K_s]

        #перевірка гори
        #знаходимо сегмент на рівні центру гравця
        seg       = wall.segment_at(int(self.world_y + self.height / 2))
        near_wall = bool(seg and seg.contains_x(mid_x))
        #гора тримає якщо: торкається стіни + тисне W/S + є витривалість
        self.on_mountain = near_wall and pressing_climb and self.stamina > 0

        #перевірка землі
        ground_top = GROUND_WORLD_Y - self.height   #Y при якому ноги торкаються землі
        if self.world_y >= ground_top and not self.on_mountain:
            self.on_ground = True
            self.world_y   = float(ground_top)   #приземлюємо гравця точно на землю
            self.vel_y     = 0.0                  #обнуляємо швидкість падіння
        else:
            self.on_ground = False

        #перевірка платформ
        self.on_platform = False
        #перевіряємо платформи лише коли гравець падає або стоїть (vel_y >= 0)
        #і не чіпляється за гору
        if self.vel_y >= 0 and not self.on_mountain:
            for plat in wall.all_platforms():
                prev_feet = feet_y - self.vel_y   #де були ноги минулого кадру
                #умова посадки: ноги перетнули верхній край платформи зверху вниз
                #і гравець знаходиться в межах ширини платформи
                if (plat.world_y <= feet_y <= plat.world_y + plat.h + 4 and
                        prev_feet <= plat.world_y + plat.h and
                        plat.x <= mid_x <= plat.x + plat.w):
                    self.world_y     = float(plat.world_y - self.height)  #садимо на платформу
                    self.vel_y       = 0.0
                    self.on_platform = True
                    break   #зупиняємось на першій знайденій платформі

        #горизонтальний рух
        if keys[pygame.K_a]:
            self.world_x  -= self.speed
            self.direction = "left"
            moving         = True
        if keys[pygame.K_d]:
            self.world_x  += self.speed
            self.direction = "right"
            moving         = True
        #не виходимо за межі екрану
        self.world_x = max(0, min(WIN_W - self.width, self.world_x))

        #вертикальна фізика
        if self.on_mountain:
            #гравець тримається за гору то гравітації нема
            self.vel_y = 0.0
            if keys[pygame.K_w]:
                self.world_y -= self.speed   #лізе вгору (Y зменшується)
                climbing      = True
            if keys[pygame.K_s]:
                self.world_y += self.speed   #лізе вниз
                climbing      = True
        elif not self.on_ground and not self.on_platform:
            #вільне падіння: не чіпляється за гору, не на землі, не на платформі
            self.vel_y   += GRAVITY          #прискорення вниз
            self.world_y += self.vel_y       #переміщення

        #витривалість
        if climbing:
            #лазіння витрачає витривалість
            self.stamina = max(0.0, self.stamina - STAMINA_DRAIN)
        elif self.on_ground or self.on_platform:
            #відпочинок на землі або платформі відновлює витривалість
            self.stamina = min(float(MAX_STAMINA), self.stamina + STAMINA_REGEN)
        #У повітрі витривалість не змінюється

        #стан анімації
        if climbing:
            self.action = "climb"
        elif moving:
            self.action = "walk"
        else:
            self.action = "idle"

    def draw(self, surface: pygame.Surface, camera_y: int):
        #малює поточний кадр анімації гравця
        key    = self._sprite_key()
        frames = self.sprites[key]

        #кожні frame_delay ігрових кадрів — наступний кадр спрайту
        self.frame_timer += 1
        if self.frame_timer >= self.frame_delay:
            self.frame_timer = 0
            self.frame       = (self.frame + 1) % len(frames)

        #малюємо спрайт (перетворюємо world_y у screen_y через camera_y)
        surface.blit(frames[self.frame % len(frames)],
                     (int(self.world_x), int(self.world_y) - camera_y))

#HUD (інтерфейс під час гри)

#параметри розташування шкали витривалості на екрані
STAMINA_BAR_W = 300   #ширина шкали
STAMINA_BAR_H = 22    #висота шкали
STAMINA_BAR_X = 20    #відступ зліва
STAMINA_BAR_Y = 55    #відступ зверху


def draw_stamina_bar(surface: pygame.Surface, stamina: float):
    """
    малює шкалу витривалості у лівому верхньому куті
    колір змінюється залежно від рівня:
      > 50%  — зелений
      > 25%  — жовтий
      <= 25% — червоний
    """
    ratio  = stamina / MAX_STAMINA   #значення від 0.0 до 1.0

    #сірий фон шкали
    pygame.draw.rect(surface, (60, 60, 60),
                     (STAMINA_BAR_X, STAMINA_BAR_Y, STAMINA_BAR_W, STAMINA_BAR_H))

    #кольорове заповнення
    fill_w = int(STAMINA_BAR_W * ratio)
    if ratio > 0.5:
        color = (50, 200, 80)    # зелений
    elif ratio > 0.25:
        color = (220, 180, 0)    # жовтий
    else:
        color = (220, 50, 50)    # червоний

    if fill_w > 0:
        pygame.draw.rect(surface, color,
                         (STAMINA_BAR_X, STAMINA_BAR_Y, fill_w, STAMINA_BAR_H))

    #біла рамка навколо шкали
    pygame.draw.rect(surface, (200, 200, 200),
                     (STAMINA_BAR_X, STAMINA_BAR_Y, STAMINA_BAR_W, STAMINA_BAR_H), 2)


def draw_ground(surface: pygame.Surface, camera_y: int):
    #малює зелену смужку землі та чорну штучку під нею
    screen_y = GROUND_WORLD_Y - camera_y   #Y землі на екрані
    if screen_y < WIN_H:   #малюємо лише якщо земля видима
        pygame.draw.rect(surface, GROUND_COLOR, (0, screen_y, WIN_W, GROUND_H))
        pygame.draw.line(surface, GROUND_BORDER, (0, screen_y), (WIN_W, screen_y), 4)
        #темна зона нижче землі
        pygame.draw.rect(surface, (20, 20, 20), (0, screen_y + GROUND_H, WIN_W, WIN_H))


def draw_hud(surface: pygame.Surface, meters: int, pname: str,
             font_big, font_small, stamina: float):
    #малює весь інтерфейс

    #висота у правому верхньому куті
    txt = f"{meters} м"
    lbl = font_big.render(txt, True, (255, 255, 255))
    surface.blit(lbl, (WIN_W - lbl.get_width() - 30, 30))

    #ім'я гравця у лівому верхньому куті
    if pname:
        surface.blit(font_small.render(pname, True, (255, 255, 255)), (20, 20))

    #підпис і шкала витривалості
    stam_lbl = font_small.render("Витривалість", True, (220, 220, 220))
    surface.blit(stam_lbl, (STAMINA_BAR_X, STAMINA_BAR_Y - 22))
    draw_stamina_bar(surface, stamina)

    #попередження якщо витривалість повністю вичерпана
    if stamina <= 0:
        warn = font_big.render("Відпочиньте на платформі!", True, (255, 80, 80))
        surface.blit(warn, (WIN_W // 2 - warn.get_width() // 2, 30))

#ЗАПУСК

def make_pause_buttons():
    """Створює три кнопки меню паузи відцентровані на екрані."""
    bw, bh = 320, 56
    bx     = WIN_W // 2 - bw // 2
    base_y = WIN_H // 2 - 60
    gap    = 72
    return (
        PauseButton("  Продовжити",      bx, base_y,           bw, bh),
        PauseButton("  Почати спочатку", bx, base_y + gap,     bw, bh),
        PauseButton("  Вийти в меню",    bx, base_y + gap * 2, bw, bh),
    )


def run_game():
    """Основний ігровий цикл. Повертає 'menu', 'restart' або 'quit'."""
    global player_name

    pygame.init()
    window     = pygame.display.set_mode((WIN_W, WIN_H))
    clock      = pygame.time.Clock()
    font_big   = pygame.font.SysFont("Arial", 42, bold=True)
    font_mid   = pygame.font.SysFont("Arial", 30, bold=True)
    font_small = pygame.font.SysFont("Arial", 24)

    wall   = MountainWall()
    player = Player(WIN_W // 2 - 35, GROUND_WORLD_Y - 100)
    clouds = create_clouds(22)   #генеруємо початковий набір хмар

    camera_y = int(player.world_y) - WIN_H // 2

    btn_continue, btn_restart, btn_main_menu = make_pause_buttons()

    paused  = False
    running = True
    result  = "quit"   #що повернути після виходу

    while running:
        mouse_pos = pygame.mouse.get_pos()

        #обробка подій
        for e in pygame.event.get():
            if e.type == QUIT:
                running = False
                result  = "quit"

            elif e.type == KEYDOWN:
                if e.key == K_ESCAPE:
                    paused = not paused   #ESC — перемикає паузу

            elif e.type == MOUSEBUTTONDOWN and e.button == 1 and paused:
                #кліки по кнопках паузи обробляємо лише коли пауза активна
                if btn_continue.is_clicked(mouse_pos):
                    paused = False
                elif btn_restart.is_clicked(mouse_pos):
                    running = False
                    result  = "restart"
                elif btn_main_menu.is_clicked(mouse_pos):
                    running = False
                    result  = "menu"

        if not paused:
            keys = pygame.key.get_pressed()
            player.update(keys, wall)

            #плавне слідування камери за гравцем
            target_cam = int(player.world_y) - WIN_H // 2
            #камера рухається на 1/8 відстані до цілі за кадр
            camera_y  += (target_cam - camera_y) // 8
            #камера не опускається нижче рівня землі
            camera_y   = min(camera_y, GROUND_WORLD_Y - WIN_H + GROUND_H + 20)

            #добудовуємо гору вгору якщо камера наближається до верху
            wall.extend_up(camera_y - 500)

            #оновлення хмар і додавання нових при підйомі
            for c in clouds:
                c.update()
            extend_clouds(clouds, camera_y)

        #рахуємо висоту у метрах (world_y < 0 = вище землі)
        meters = max(0, int((0 - player.world_y) / PIXELS_PER_METER))

        #МАЛЮВАННЯ
        #небо з градієнтом залежно від висоти — чим вище тим темніше і синіше
        sky_top    = max(0, min(255, 100 - meters // 10))
        sky_mid    = max(0, min(255, 155 - meters // 8))
        sky_bottom = max(0, min(255, 220 - meters // 5))
        window.fill((sky_top, sky_mid, sky_bottom))

        #хмари малюємо ДО гори і гравця щоб вони були на задньому плані
        for c in clouds:
            c.draw(window, camera_y)

        draw_ground(window, camera_y)        #земля
        wall.draw(window, camera_y)          #гора
        player.draw(window, camera_y)        #гравець
        draw_hud(window, meters, player_name, font_big, font_small, player.stamina)  #HUD

        if paused:
            draw_pause_menu(window, font_big, font_mid, mouse_pos,
                            btn_continue, btn_restart, btn_main_menu)

        pygame.display.update()
        clock.tick(60)

    pygame.quit()
    return result



#ГОЛОВНИЙ ЦИКЛ ПРОГРАМИ


while True:
    show_menu()
    if not game_started:
        break   #гравець натиснув "Вихід" у головному меню

    action = run_game()

    if action == "quit":
        break          #закрити програму
    elif action == "menu":
        game_started = False   #покажемо головне меню знову
        continue
    elif action == "restart":
        continue       #перезапустити гру з тим самим іменем (меню не показуємо)