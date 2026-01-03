import pygame
import random
import json
import os
import array
import math

# --- 初始化 Pygame 與 音效 ---
pygame.mixer.pre_init(44100, -16, 1, 512)
pygame.init()
pygame.mixer.init()

# --- 設定視窗 ---
WIDTH, HEIGHT = 600, 800
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("打地鼠 (Whac-A-Mole) - 極致打擊感版")

# --- 音樂檔案設定 ---
MUSIC_MENU = "menu.mp3"
MUSIC_GAME = "game.mp3"

# --- 色彩定義 ---
GRASS_BASE = (126, 200, 80)
GRASS_FEVER = (200, 100, 80)  # Fever 模式背景色
WOOD_MAIN = (205, 133, 63)
WOOD_LIGHT = (222, 184, 135)
WOOD_BORDER = (101, 67, 33)
MUD_LIGHT = (160, 110, 60)
MUD_DARK = (120, 80, 40)
HOLE_BLACK = (40, 20, 10)
SLIDER_BG = (80, 50, 20)
SLIDER_FILL = (255, 200, 0)
TEXT_YELLOW = (255, 223, 0)
TEXT_OUTLINE = (50, 30, 0)
BTN_PAUSE_BG = (200, 150, 80)

# 地鼠配色
MOLE_SKIN_NORMAL = (180, 120, 60)
MOLE_SKIN_SILVER = (192, 192, 205)
MOLE_SKIN_GOLD = (255, 215, 0)
MOLE_SNOUT = (255, 228, 196)
MOLE_NOSE = (255, 60, 60)
MOLE_BLUSH = (255, 140, 140)
MOLE_EAR_INNER = (230, 180, 140)

# --- 槌子造型定義 ---
HAMMER_SKINS = {
    "default": {"name": "經典鐵槌", "price": 0, "c_handle": (139, 69, 19), "c_head": (80, 80, 80),
                "c_detail": (200, 200, 200)},
    "gold": {"name": "土豪金槌", "price": 100, "c_handle": (100, 0, 0), "c_head": (255, 215, 0),
             "c_detail": (255, 250, 200)},
    "cyber": {"name": "霓虹科技", "price": 100, "c_handle": (20, 20, 50), "c_head": (0, 255, 255),
              "c_detail": (255, 0, 255)},
    "toy": {"name": "玩具氣球", "price": 100, "c_handle": (255, 255, 0), "c_head": (255, 100, 150),
            "c_detail": (100, 255, 100)}
}

# --- 遊戲參數 ---
FPS = 60
GRID_ROWS = 3
GRID_COLS = 3
HOLE_WIDTH = 140
HOLE_HEIGHT = 100
MARGIN_Y = 220
SPACING_X = (WIDTH - (GRID_COLS * HOLE_WIDTH)) // (GRID_COLS + 1)
SPACING_Y = (HEIGHT - MARGIN_Y - 50 - (GRID_ROWS * HOLE_HEIGHT)) // (GRID_ROWS + 1)

# --- 全局變數 ---
sound_enabled = True
vibration_enabled = True
bgm_channel = None
generated_bgm = None
current_music_file = None
vol_bgm_level = 0.5
vol_sfx_level = 1.0

# 震動變數
screen_shake = 0

# 用戶資料存檔
USER_DATA_FILE = "userdata.json"
user_data = {"coins": 0, "current_skin": "default", "owned_skins": ["default"]}


def load_userdata():
    global user_data
    if os.path.exists(USER_DATA_FILE):
        try:
            with open(USER_DATA_FILE, "r") as f:
                user_data.update(json.load(f))
        except:
            pass


def save_userdata():
    try:
        with open(USER_DATA_FILE, "w") as f:
            json.dump(user_data, f)
    except:
        pass


# 排行榜存檔
LEADERBOARD_FILE = "leaderboard.json"
leaderboard_scores = []


def load_leaderboard():
    global leaderboard_scores
    if os.path.exists(LEADERBOARD_FILE):
        try:
            with open(LEADERBOARD_FILE, "r") as f:
                leaderboard_scores = json.load(f)
        except:
            leaderboard_scores = []


def save_to_leaderboard(new_score):
    global leaderboard_scores
    leaderboard_scores.append(new_score)
    leaderboard_scores.sort(reverse=True)
    leaderboard_scores = leaderboard_scores[:5]
    try:
        with open(LEADERBOARD_FILE, "w") as f:
            json.dump(leaderboard_scores, f)
    except:
        pass


load_userdata()
load_leaderboard()


# --- 字型 ---
def get_font(size):
    possible_fonts = ['microsoftjhenghei', 'simhei', 'arial', 'pingfang']
    return pygame.font.SysFont(possible_fonts, size)


font_xl = get_font(60)
font_large = get_font(45)
font_medium = get_font(35)
font_small = get_font(25)
font_tiny = get_font(20)


# --- 緩動函數 ---
def ease_out_back(x):
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * math.pow(x - 1, 3) + c1 * math.pow(x - 1, 2)


# --- 音效生成 ---
def create_sound(freq_start, freq_end, duration, volume=0.5):
    sample_rate = 44100
    n_samples = int(sample_rate * duration)
    buffer = array.array('h')
    for i in range(n_samples):
        t = i / n_samples
        freq = freq_start + (freq_end - freq_start) * t
        val = int(32767 * volume * (0.5 + 0.5 * math.sin(2 * math.pi * i * freq / sample_rate)))
        buffer.append(val)
    return pygame.mixer.Sound(buffer)


def update_sfx_volume():
    for s in [snd_hit, snd_hit_silver, snd_hit_gold, snd_start, snd_win, snd_lose, snd_coin, snd_fever]:
        s.set_volume(vol_sfx_level)


def update_bgm_volume():
    if sound_enabled:
        pygame.mixer.music.set_volume(vol_bgm_level)
    else:
        pygame.mixer.music.set_volume(0)
    if bgm_channel and generated_bgm:
        generated_bgm.set_volume(vol_bgm_level * 0.6 if sound_enabled else 0)


# --- 繪製函式 ---
def draw_text_with_outline(surface, text, font, color, outline_color, pos, align="center"):
    text_surf = font.render(str(text), True, color)
    outline_surf = font.render(str(text), True, outline_color)
    w, h = text_surf.get_size()
    x, y = pos
    if align == "center":
        x -= w // 2; y -= h // 2
    elif align == "right":
        x -= w
    for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2), (-2, -2), (2, 2)]:
        surface.blit(outline_surf, (x + dx, y + dy))
    surface.blit(text_surf, (x, y))


def draw_button_3d(surface, rect, text, base_color):
    pygame.draw.rect(surface, (base_color[0] // 2, base_color[1] // 2, base_color[2] // 2),
                     (rect.x, rect.y + 6, rect.w, rect.h), border_radius=15)
    pygame.draw.rect(surface, base_color, rect, border_radius=15)
    pygame.draw.rect(surface, (255, 255, 255), rect, 2, border_radius=15)
    draw_text_with_outline(surface, text, font_medium, (255, 255, 255), (0, 0, 0), (rect.centerx, rect.centery))


def draw_wood_board(surface):
    rect = pygame.Rect(10, 10, WIDTH - 20, 180)
    pygame.draw.rect(surface, (50, 30, 10), (15, 15, WIDTH - 20, 180), border_radius=20)
    pygame.draw.rect(surface, WOOD_MAIN, rect, border_radius=20)
    for i in range(30, 180, 30):
        pygame.draw.line(surface, WOOD_LIGHT, (20, i + 10), (WIDTH - 20, i + 10), 3)
        pygame.draw.line(surface, WOOD_BORDER, (20, i + 12), (WIDTH - 20, i + 12), 1)
    pygame.draw.rect(surface, WOOD_BORDER, rect, 5, border_radius=20)


def draw_slider(surface, x, y, width, height, label, value):
    draw_text_with_outline(surface, label, font_small, (255, 255, 255), (0, 0, 0), (x + width // 2, y - 25))
    rect_bg = pygame.Rect(x, y, width, height)
    pygame.draw.rect(surface, SLIDER_BG, rect_bg, border_radius=5)
    fill_width = int(width * value)
    if fill_width > 0:
        pygame.draw.rect(surface, SLIDER_FILL, (x, y, fill_width, height), border_radius=5)
    return rect_bg


def draw_settings_icon(surface, x, y, size=60):
    rect = pygame.Rect(x, y, size, size)
    pygame.draw.rect(surface, (220, 220, 220), rect, border_radius=15)
    pygame.draw.rect(surface, (100, 100, 100), rect, 3, border_radius=15)
    cx, cy = rect.centerx, rect.centery
    pygame.draw.circle(surface, (80, 80, 80), (cx, cy), 18)
    pygame.draw.circle(surface, (220, 220, 220), (cx, cy), 8)
    for i in range(0, 360, 45):
        rad = math.radians(i)
        sx = cx + math.cos(rad) * 22
        sy = cy + math.sin(rad) * 22
        pygame.draw.circle(surface, (80, 80, 80), (sx, sy), 5)
    return rect


def draw_shop_button(surface, x, y):
    rect = pygame.Rect(x, y, 60, 60)
    pygame.draw.rect(surface, (255, 200, 100), rect, border_radius=15)
    pygame.draw.rect(surface, (200, 100, 0), rect, 3, border_radius=15)
    draw_text_with_outline(surface, "$", font_large, (255, 255, 255), (0, 0, 0), (rect.centerx, rect.centery))
    return rect


# --- ★★★ 更新：設定視窗 (拉高並調整間距) ★★★ ---
def draw_settings_window(surface):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    surface.blit(overlay, (0, 0))

    # 拉高面板高度，讓內容更寬鬆 (520 -> 550)
    panel_h = 550
    panel_y = (HEIGHT - panel_h) // 2
    pygame.draw.rect(surface, WOOD_MAIN, ((WIDTH - 400) // 2, panel_y, 400, panel_h), border_radius=20)
    pygame.draw.rect(surface, WOOD_BORDER, ((WIDTH - 400) // 2, panel_y, 400, panel_h), 6, border_radius=20)

    draw_text_with_outline(surface, "遊戲設定", font_xl, TEXT_YELLOW, TEXT_OUTLINE, (WIDTH // 2, panel_y + 40))

    # 調整 Y 軸間距，使其均勻分佈
    # 音效按鈕
    mute_rect = pygame.Rect(WIDTH // 2 - 80, panel_y + 110, 160, 50)
    c_btn = (100, 200, 100) if sound_enabled else (200, 80, 80)
    draw_button_3d(surface, mute_rect, "音效: 開" if sound_enabled else "音效: 關", c_btn)

    # 震動按鈕
    vib_rect = pygame.Rect(WIDTH // 2 - 80, panel_y + 180, 160, 50)
    c_vib = (100, 200, 100) if vibration_enabled else (200, 80, 80)
    draw_button_3d(surface, vib_rect, "震動: 開" if vibration_enabled else "震動: 關", c_vib)

    # 滑桿
    rect_bgm = draw_slider(surface, (WIDTH - 300) // 2, panel_y + 270, 300, 20,
                           f"音樂 (BGM): {int(vol_bgm_level * 100)}%", vol_bgm_level)
    rect_sfx = draw_slider(surface, (WIDTH - 300) // 2, panel_y + 350, 300, 20,
                           f"音效 (SFX): {int(vol_sfx_level * 100)}%", vol_sfx_level)

    # 關閉按鈕
    close_rect = pygame.Rect(WIDTH // 2 - 60, panel_y + 450, 120, 50)
    draw_button_3d(surface, close_rect, "確 定", (200, 150, 50))

    return mute_rect, vib_rect, rect_bgm, rect_sfx, close_rect


# --- BGM 邏輯 ---
def play_bgm(target_file):
    global current_music_file, bgm_channel, generated_bgm
    if current_music_file == target_file and pygame.mixer.music.get_busy(): return
    if os.path.exists(target_file):
        try:
            if bgm_channel: bgm_channel.stop()
            pygame.mixer.music.load(target_file)
            pygame.mixer.music.play(-1)
            update_bgm_volume()
            current_music_file = target_file
            return
        except:
            pass

    if current_music_file == "DEFAULT": return
    sample_rate = 44100
    duration = 4.0
    n_samples = int(sample_rate * duration)
    buffer = array.array('h')
    notes = [261.63, 329.63, 392.00, 523.25]
    note_len = n_samples // 8
    for i in range(n_samples):
        idx = (i // note_len) % 4
        freq = notes[idx]
        val = int(32767 * 0.1 * math.sin(2 * math.pi * i * freq / sample_rate))
        buffer.append(int(val))
    generated_bgm = pygame.mixer.Sound(buffer)
    bgm_channel = pygame.mixer.Channel(7)
    bgm_channel.play(generated_bgm, loops=-1)
    update_bgm_volume()
    current_music_file = "DEFAULT"


def toggle_music_enabled(enabled):
    global sound_enabled
    sound_enabled = enabled
    update_bgm_volume()
    if not pygame.mixer.music.get_busy() and current_music_file and current_music_file != "DEFAULT":
        pygame.mixer.music.play(-1)


# 音效建立
snd_hit = create_sound(600, 300, 0.1)
snd_hit_silver = create_sound(800, 400, 0.1)
snd_hit_gold = create_sound(1000, 500, 0.15)
snd_coin = create_sound(1500, 2000, 0.1, 0.3)
snd_start = create_sound(400, 800, 0.3)
snd_win = create_sound(400, 600, 0.2)
snd_lose = create_sound(800, 200, 0.5)
snd_fever = create_sound(300, 800, 0.5, 0.4)  # Fever音效

update_sfx_volume()
play_bgm(MUSIC_MENU)


def play_sfx(sound):
    if sound_enabled: sound.play()


# --- 浮動文字類別 ---
class FloatingText:
    def __init__(self, x, y, text, color=(255, 255, 0), size="medium"):
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.life = 60
        self.dy = -1.5
        self.size = size

    def update(self):
        self.y += self.dy
        self.life -= 1
        return self.life > 0

    def draw(self, surface):
        alpha = min(255, self.life * 5)
        f = font_large if self.size == "large" else font_medium
        txt_surf = f.render(str(self.text), True, self.color)
        txt_surf.set_alpha(alpha)
        surface.blit(txt_surf, (self.x - txt_surf.get_width() // 2, self.y))


# --- 打擊特效類別 ---
class HitBurst:
    def __init__(self, x, y, is_combo=False):
        self.x = x
        self.y = y
        self.life = 20
        self.max_life = 20
        self.radius = 10
        self.color = (255, 100, 50) if is_combo else (255, 255, 200)

    def update(self):
        self.life -= 1
        self.radius += 3
        return self.life > 0

    def draw(self, surface):
        if self.life > 0:
            alpha = int(255 * (self.life / self.max_life))
            s_circle = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(s_circle, (*self.color, alpha), (self.radius, self.radius), self.radius, 4)
            surface.blit(s_circle, (self.x - self.radius, self.y - self.radius))

            num_spikes = 8
            angle_step = 360 / num_spikes
            for i in range(num_spikes):
                angle = math.radians(i * angle_step + (20 - self.life) * 10)
                start_dist = self.radius * 0.8
                end_dist = self.radius * 1.6
                sx = self.x + math.cos(angle) * start_dist
                sy = self.y + math.sin(angle) * start_dist
                ex = self.x + math.cos(angle) * end_dist
                ey = self.y + math.sin(angle) * end_dist
                pygame.draw.line(surface, (*self.color, alpha), (sx, sy), (ex, ey), 3)


floating_texts = []
hit_effects = []


# --- 動態槌子類別 ---
class DynamicHammer:
    def __init__(self):
        self.angle = 0
        self.target_angle = 0
        self.swing_speed = 30  # 揮動速度
        self.is_swinging = False
        self.state = "IDLE"  # IDLE, UP, DOWN

    def swing(self):
        # 狀態機：點擊時先舉起 (UP)
        if self.state == "IDLE":
            self.state = "UP"
            self.target_angle = 50

    def reset(self):
        # 放開滑鼠時揮下 (DOWN)
        self.state = "DOWN"
        self.target_angle = -45

    def update(self):
        # 角度趨近邏輯 (避免來回震盪)
        diff = self.target_angle - self.angle

        if abs(diff) <= self.swing_speed:
            self.angle = self.target_angle
            # 到達目標後的狀態切換
            if self.state == "UP":
                pass  # 舉起後保持
            elif self.state == "DOWN":
                # 揮下去後，自動慢慢回到原點
                self.target_angle = 0
                self.state = "IDLE"
            elif self.state == "IDLE":
                self.angle = 0
        else:
            # 根據方向移動
            if diff > 0:
                self.angle += self.swing_speed
            else:
                self.angle -= self.swing_speed

    def draw(self, surface, x, y):
        # 建立一個暫存圖層來繪製槌子
        sid = user_data['current_skin']
        skin = HAMMER_SKINS.get(sid, HAMMER_SKINS['default'])

        surf_w, surf_h = 150, 150
        hammer_surf = pygame.Surface((surf_w, surf_h), pygame.SRCALPHA)

        cx, cy = surf_w // 2, surf_h // 2 + 30

        c_h = skin['c_handle']
        c_head = skin['c_head']
        c_d = skin['c_detail']

        # 繪製槌子組件
        pygame.draw.rect(hammer_surf, c_h, (cx - 10, cy - 50, 20, 100), border_radius=5)
        pygame.draw.rect(hammer_surf, c_head, (cx - 40, cy - 70, 80, 50), border_radius=10)
        pygame.draw.rect(hammer_surf, c_d, (cx - 35, cy - 65, 70, 10), border_radius=5)

        # 旋轉
        rotated_surf = pygame.transform.rotate(hammer_surf, self.angle)

        # 修正中心點偏移
        rect = rotated_surf.get_rect(center=(x + 15, y + 15))
        surface.blit(rotated_surf, rect.topleft)


# ==========================================
# 遊戲物件
# ==========================================

class Particle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = random.uniform(-3, 3)
        self.vy = random.uniform(-5, -2)
        self.life = 1.0
        self.size = random.randint(5, 9)
        self.color = (180, 160, 120)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.2
        self.life -= 0.05
        self.size *= 0.9
        return self.life > 0

    def draw(self, surface):
        if self.life > 0:
            s = pygame.Surface((int(self.size * 2), int(self.size * 2)), pygame.SRCALPHA)
            alpha = int(self.life * 255)
            pygame.draw.circle(s, (*self.color, alpha), (int(self.size), int(self.size)), int(self.size))
            surface.blit(s, (self.x - self.size, self.y - self.size))


class Hole:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, HOLE_WIDTH, HOLE_HEIGHT)
        self.is_up = False
        self.up_start_time = 0
        self.hit = False
        self.stay_time = 800
        self.anim_progress = 0.0
        self.particles = []
        self.mole_type = 'normal'

    def pop_up(self, stay_duration):
        if not self.is_up:
            self.is_up = True
            self.hit = False
            self.stay_time = stay_duration
            self.up_start_time = pygame.time.get_ticks()
            self.anim_progress = 0.0

            rand = random.random()
            if rand < 0.1:
                self.mole_type = 'gold'
            elif rand < 0.3:
                self.mole_type = 'silver'
            else:
                self.mole_type = 'normal'

            for _ in range(6):
                self.particles.append(Particle(self.rect.centerx, self.rect.centery))

    def get_score(self):
        if self.mole_type == 'gold':
            return 3
        elif self.mole_type == 'silver':
            return 2
        else:
            return 1

    def update(self):
        if game_state == "PAUSED": return
        self.particles = [p for p in self.particles if p.update()]
        if self.is_up and not self.hit:
            if pygame.time.get_ticks() - self.up_start_time > self.stay_time + 200:
                self.is_up = False
        elif self.hit:
            if pygame.time.get_ticks() - self.up_start_time > 300:
                self.is_up = False

    def draw(self, surface):
        pygame.draw.ellipse(surface, MUD_DARK, (self.rect.x - 10, self.rect.y - 5, HOLE_WIDTH + 20, HOLE_HEIGHT + 15))
        pygame.draw.ellipse(surface, MUD_LIGHT, (self.rect.x - 5, self.rect.y, HOLE_WIDTH + 10, HOLE_HEIGHT + 5))
        hole_inner_rect = pygame.Rect(self.rect.x + 5, self.rect.y + 10, HOLE_WIDTH - 10, HOLE_HEIGHT - 10)
        pygame.draw.ellipse(surface, HOLE_BLACK, hole_inner_rect)

        self.draw_mole(surface)

        rim_rect = pygame.Rect(self.rect.x - 5, self.rect.y + 10, HOLE_WIDTH + 10, HOLE_HEIGHT)
        pygame.draw.arc(surface, MUD_LIGHT, rim_rect, 3.14, 6.28, 20)
        pygame.draw.arc(surface, MUD_DARK, rim_rect, 3.14, 6.28, 5)

        for p in self.particles: p.draw(surface)

    def draw_mole(self, surface):
        current_time = pygame.time.get_ticks()
        if game_state in ["PAUSED", "SETTINGS", "SHOP"]:
            pass
        else:
            elapsed = current_time - self.up_start_time
            pop_duration = 200
            if not self.is_up and elapsed > self.stay_time + 300:
                self.anim_progress = 0
                return

            if elapsed < pop_duration:
                self.anim_progress = ease_out_back(elapsed / pop_duration)
            elif elapsed > self.stay_time:
                back_elapsed = elapsed - self.stay_time
                self.anim_progress = 1.0 - (back_elapsed / 200)
            elif self.hit:
                self.anim_progress = 1.0
            else:
                self.anim_progress = 1.0

        self.anim_progress = max(0, min(1.2, self.anim_progress))
        mole_h_max = HOLE_HEIGHT * 1.35
        mole_h = mole_h_max * self.anim_progress

        clip_rect = pygame.Rect(self.rect.x, self.rect.y - 150, HOLE_WIDTH, HOLE_HEIGHT + 150)
        old_clip = surface.get_clip()
        surface.set_clip(clip_rect)

        if self.mole_type == 'gold':
            body_color = MOLE_SKIN_GOLD
        elif self.mole_type == 'silver':
            body_color = MOLE_SKIN_SILVER
        else:
            body_color = MOLE_SKIN_NORMAL

        mw = HOLE_WIDTH * 0.75
        mh = mole_h_max
        mx = self.rect.centerx - mw / 2
        my = self.rect.centery + 30 - mole_h

        # Mole Body
        pygame.draw.circle(surface, body_color, (mx + 12, my + 18), 24)
        pygame.draw.circle(surface, MOLE_EAR_INNER, (mx + 12, my + 18), 16)
        pygame.draw.circle(surface, body_color, (mx + mw - 12, my + 18), 24)
        pygame.draw.circle(surface, MOLE_EAR_INNER, (mx + mw - 12, my + 18), 16)
        pygame.draw.rect(surface, body_color, (mx, my, mw, mh), border_radius=int(mw // 2))

        face_cx = mx + mw / 2
        face_cy = my + mh * 0.42
        snout_w, snout_h = mw * 0.6, mh * 0.35
        pygame.draw.ellipse(surface, MOLE_SNOUT, (face_cx - snout_w / 2, face_cy - 2, snout_w, snout_h))
        pygame.draw.ellipse(surface, MOLE_NOSE, (face_cx - 16, face_cy - 10, 32, 24))
        pygame.draw.circle(surface, (255, 200, 200), (face_cx - 6, face_cy - 2), 5)

        if not self.hit:
            pygame.draw.arc(surface, (70, 40, 10), (face_cx - 8, face_cy + 15, 8, 8), 3.14, 6.28, 2)
            pygame.draw.arc(surface, (70, 40, 10), (face_cx, face_cy + 15, 8, 8), 3.14, 6.28, 2)
            pygame.draw.rect(surface, (255, 255, 255), (face_cx - 3, face_cy + 23, 6, 6), border_radius=1)

        eye_y = face_cy - 12
        eye_off = mw * 0.24

        if self.hit:
            draw_text_with_outline(surface, "X", font_medium, (60, 30, 0), (255, 255, 255), (face_cx - eye_off, eye_y))
            draw_text_with_outline(surface, "X", font_medium, (60, 30, 0), (255, 255, 255), (face_cx + eye_off, eye_y))
        else:
            pygame.draw.circle(surface, (20, 10, 0), (face_cx - eye_off, eye_y), 10)
            pygame.draw.circle(surface, (20, 10, 0), (face_cx + eye_off, eye_y), 10)
            pygame.draw.circle(surface, (255, 255, 255), (face_cx - eye_off - 3, eye_y - 4), 4)
            pygame.draw.circle(surface, (255, 255, 255), (face_cx + eye_off - 3, eye_y - 4), 4)

        surface.set_clip(old_clip)

    def check_click(self, pos):
        if self.is_up and not self.hit and self.anim_progress > 0.5:
            mole_h_max = HOLE_HEIGHT * 1.35
            base_y = self.rect.centery + 30
            head_y = base_y - mole_h_max * self.anim_progress
            click_rect = pygame.Rect(self.rect.x + 10, head_y, HOLE_WIDTH - 20, mole_h_max * 0.9)
            if click_rect.collidepoint(pos):
                self.hit = True
                self.up_start_time = pygame.time.get_ticks()
                return True
        return False


# --- 關卡資料 (累積目標 3000 分) ---
LEVELS = [
    # Lv 1-3: 新手期 (累積 450 分)
    {"level": 1, "target": 100, "time": 30, "speed": 1000, "appear": 800},
    {"level": 2, "target": 250, "time": 30, "speed": 900, "appear": 700},
    {"level": 3, "target": 450, "time": 30, "speed": 850, "appear": 650},

    # Lv 4-6: 進階期 (累積 1350 分，時間延長至 40秒)
    {"level": 4, "target": 700, "time": 40, "speed": 800, "appear": 600},
    {"level": 5, "target": 1000, "time": 40, "speed": 700, "appear": 550},
    {"level": 6, "target": 1350, "time": 40, "speed": 650, "appear": 500},

    # Lv 7-9: 高手期 (累積 2550 分，速度很快)
    {"level": 7, "target": 1750, "time": 45, "speed": 600, "appear": 450},
    {"level": 8, "target": 2150, "time": 45, "speed": 550, "appear": 400},
    {"level": 9, "target": 2550, "time": 45, "speed": 500, "appear": 350},

    # Lv 10: 最終挑戰 (目標 3000 分，極限速度)
    {"level": 10, "target": 3000, "time": 50, "speed": 400, "appear": 250},
]

# 全局變數
game_state = "MENU"
game_mode = "ENDLESS"
score = 0
start_time = 0
pause_start_time = 0
last_mole_time = 0
current_level_idx = 0
current_target = 0
current_duration = 0
mole_speed = 800
mole_appear_rate = 600
score_saved = False

# --- Combo 與 Fever 變數 ---
combo_count = 0
is_fever_mode = False
last_hit_time = 0  # 用於紀錄最後打擊時間 (5秒重置連擊)
fever_start_time = 0  # 用於紀錄 Fever 開始時間 (10秒結束 Fever)

hole_list = []
for row in range(GRID_ROWS):
    for col in range(GRID_COLS):
        x = SPACING_X + col * (HOLE_WIDTH + SPACING_X)
        y = MARGIN_Y + 10 + SPACING_Y + row * (HOLE_HEIGHT + SPACING_Y)
        hole_list.append(Hole(x, y))

# --- 裝飾物 ---
decorations = []
for _ in range(15):
    dx = random.randint(20, WIDTH - 20)
    dy = random.randint(MARGIN_Y + 20, HEIGHT - 20)
    color = random.choice([(255, 255, 255), (255, 200, 200), (255, 255, 150)])
    decorations.append({'type': 'flower', 'x': dx, 'y': dy, 'color': color})

hammer = DynamicHammer()  # 實例化槌子


def draw_background_scene(surface):
    # Fever 模式背景變色
    bg_color = GRASS_FEVER if is_fever_mode else GRASS_BASE
    surface.fill(bg_color)

    for deco in decorations:
        if deco['type'] == 'flower':
            x, y = deco['x'], deco['y']
            pygame.draw.circle(surface, deco['color'], (x - 5, y), 5)
            pygame.draw.circle(surface, deco['color'], (x + 5, y), 5)
            pygame.draw.circle(surface, deco['color'], (x, y - 5), 5)
            pygame.draw.circle(surface, deco['color'], (x, y + 5), 5)
            pygame.draw.circle(surface, (255, 255, 0), (x, y), 4)


# --- 獨立的 Combo 繪製函式 (位置在下方) ---
def draw_combo_ui(surface):
    # 只有大於 1 才顯示
    if combo_count > 1:
        c_txt = f"COMBO x{combo_count}"
        # 根據 Combo 數量放大字體
        scale = min(1.5, 1.0 + (combo_count * 0.05))
        f = pygame.font.SysFont(['arial', 'microsoftjhenghei'], int(50 * scale), bold=True)

        # 文字震動效果
        off_x = random.randint(-2, 2) if is_fever_mode else 0
        off_y = random.randint(-2, 2) if is_fever_mode else 0

        # 顏色設定
        col = (255, 50, 50) if is_fever_mode else (255, 200, 0)
        out = (255, 255, 255) if is_fever_mode else (50, 30, 0)

        # 顯示在下方 (HEIGHT - 100)
        draw_text_with_outline(surface, c_txt, f, col, out, (WIDTH // 2 + off_x, HEIGHT - 100 + off_y))

    if is_fever_mode:
        draw_text_with_outline(surface, "FEVER TIME!!", font_large, (255, 0, 0), (255, 255, 255),
                               (WIDTH // 2, HEIGHT - 50))


def draw_hud_ui(surface):
    draw_wood_board(surface)
    draw_text_with_outline(surface, f"得分: {int(score)}", font_large, TEXT_YELLOW, TEXT_OUTLINE, (30, 40),
                           align="left")
    draw_text_with_outline(surface, f"$ {user_data['coins']}", font_large, (255, 200, 50), TEXT_OUTLINE, (30, 90),
                           align="left")

    if game_mode == "LEVEL":
        draw_text_with_outline(surface, f"關卡: {current_level_idx + 1}", font_medium, (255, 255, 255), TEXT_OUTLINE,
                               (WIDTH // 2 + 20, 55))
        draw_text_with_outline(surface, f"目標: {current_target}", font_medium, (255, 255, 255), TEXT_OUTLINE,
                               (WIDTH // 2, 95))
    else:
        draw_text_with_outline(surface, "無盡模式", font_medium, (255, 255, 255), TEXT_OUTLINE, (WIDTH // 2 + 20, 55))
        top_score = leaderboard_scores[0] if leaderboard_scores else 0
        draw_text_with_outline(surface, f"最高: {top_score}", font_medium, (255, 200, 100), TEXT_OUTLINE,
                               (WIDTH // 2, 95))

    if game_state == "PAUSED":
        elapsed = (pause_start_time - start_time) // 1000
    else:
        elapsed = (pygame.time.get_ticks() - start_time) // 1000
    time_left = max(0, current_duration - elapsed)
    t_color = TEXT_YELLOW
    if time_left <= 10:
        if time_left % 2 == 0:
            t_color = (255, 50, 50)
        else:
            t_color = (255, 150, 150)
    draw_text_with_outline(surface, f"時間: {time_left}", font_large, t_color, TEXT_OUTLINE, (WIDTH - 30, 55),
                           align="right")

    pause_rect = pygame.Rect(WIDTH - 100, 120, 80, 40)
    pygame.draw.rect(surface, BTN_PAUSE_BG, pause_rect, border_radius=10)
    pygame.draw.rect(surface, (100, 50, 0), pause_rect, 3, border_radius=10)
    draw_text_with_outline(surface, "暫停", font_small, (255, 255, 255), (0, 0, 0),
                           (pause_rect.centerx, pause_rect.centery))
    return pause_rect


def draw_popup(surface, title, msg, btn1_txt, btn2_txt):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150))
    surface.blit(overlay, (0, 0))
    panel_h = 320
    panel_y = (HEIGHT - panel_h) // 2
    panel = pygame.Rect(50, panel_y, WIDTH - 100, panel_h)
    pygame.draw.rect(surface, WOOD_MAIN, panel, border_radius=20)
    pygame.draw.rect(surface, WOOD_BORDER, panel, 5, border_radius=20)
    draw_text_with_outline(surface, title, font_xl, TEXT_YELLOW, TEXT_OUTLINE, (WIDTH // 2, panel_y + 50))
    draw_text_with_outline(surface, msg, font_medium, (255, 255, 255), TEXT_OUTLINE, (WIDTH // 2, panel_y + 110))
    btn1 = pygame.Rect(WIDTH // 2 - 100, panel_y + 160, 200, 50)
    draw_button_3d(surface, btn1, btn1_txt, (60, 180, 60))
    btn2 = pygame.Rect(WIDTH // 2 - 100, panel_y + 230, 200, 50)
    draw_button_3d(surface, btn2, btn2_txt, (200, 80, 80))
    return btn1, btn2


def draw_leaderboard_popup(surface):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150))
    surface.blit(overlay, (0, 0))
    panel_h = 450
    panel_y = (HEIGHT - panel_h) // 2
    panel = pygame.Rect(50, panel_y, WIDTH - 100, panel_h)
    pygame.draw.rect(surface, WOOD_MAIN, panel, border_radius=20)
    pygame.draw.rect(surface, WOOD_BORDER, panel, 5, border_radius=20)
    draw_text_with_outline(surface, "歷史排行", font_xl, TEXT_YELLOW, TEXT_OUTLINE, (WIDTH // 2, panel_y + 50))
    start_y = panel_y + 110
    for i in range(5):
        s = leaderboard_scores[i] if i < len(leaderboard_scores) else 0
        c = (255, 215, 0) if i == 0 else (255, 255, 255)
        txt = f"第 {i + 1} 名 : {int(s)}"
        draw_text_with_outline(surface, txt, font_medium, c, TEXT_OUTLINE, (WIDTH // 2, start_y + i * 45))
    btn_close = pygame.Rect(WIDTH // 2 - 100, panel_y + 360, 200, 60)
    draw_button_3d(surface, btn_close, "關閉", (200, 80, 80))
    return btn_close


def draw_shop_window(surface):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150))
    surface.blit(overlay, (0, 0))
    panel_h = 550
    panel_y = (HEIGHT - panel_h) // 2
    panel = pygame.Rect(40, panel_y, WIDTH - 80, panel_h)
    pygame.draw.rect(surface, WOOD_MAIN, panel, border_radius=20)
    pygame.draw.rect(surface, WOOD_BORDER, panel, 6, border_radius=20)

    draw_text_with_outline(surface, "外觀商店", font_xl, TEXT_YELLOW, TEXT_OUTLINE, (WIDTH // 2, panel_y + 40))
    draw_text_with_outline(surface, f"持有金幣: {user_data['coins']}", font_medium, (255, 200, 50), TEXT_OUTLINE,
                           (WIDTH // 2, panel_y + 90))

    skin_buttons = {}

    grid_start_y = panel_y + 120
    grid_x = [panel.x + 30, panel.x + panel.w // 2 + 10]
    grid_y = [grid_start_y, grid_start_y + 165]

    keys = list(HAMMER_SKINS.keys())

    for i in range(4):
        k = keys[i]
        info = HAMMER_SKINS[k]
        col = i % 2
        row = i // 2

        box_rect = pygame.Rect(grid_x[col], grid_y[row], 220, 150)

        bg_c = (200, 200, 200)
        if user_data['current_skin'] == k:
            bg_c = (150, 255, 150)
        elif k in user_data['owned_skins']:
            bg_c = (200, 230, 255)

        pygame.draw.rect(surface, bg_c, box_rect, border_radius=10)
        pygame.draw.rect(surface, (100, 100, 100), box_rect, 2, border_radius=10)

        draw_hammer_preview(surface, box_rect.centerx, box_rect.y + 50, k)
        draw_text_with_outline(surface, info['name'], font_small, (0, 0, 0), (255, 255, 255),
                               (box_rect.centerx, box_rect.y + 15))

        btn_rect = pygame.Rect(box_rect.x + 20, box_rect.y + 90, box_rect.w - 40, 30)
        btn_col = (180, 180, 180)
        btn_label = "裝 備"

        if k not in user_data['owned_skins']:
            btn_label = "購 買"
            if user_data['coins'] >= info['price']:
                btn_col = (100, 200, 100)
            else:
                btn_col = (200, 100, 100)

            draw_text_with_outline(surface, f"$ {info['price']}", font_small, (255, 215, 0), (0, 0, 0),
                                   (box_rect.centerx, box_rect.y + 135))
        else:
            if user_data['current_skin'] == k:
                btn_col = (100, 150, 255)
                btn_label = "使用中"
            else:
                btn_col = (200, 200, 100)
                btn_label = "裝 備"

        draw_button_3d(surface, btn_rect, btn_label, btn_col)
        skin_buttons[k] = btn_rect

    close_rect = pygame.Rect(WIDTH // 2 - 60, panel_y + 470, 120, 50)
    draw_button_3d(surface, close_rect, "返 回", (200, 80, 80))
    return skin_buttons, close_rect


# --- 邏輯控制 ---
def start_game(mode):
    global game_state, game_mode, score, start_time, current_level_idx, score_saved
    global current_target, current_duration, mole_speed, mole_appear_rate
    global combo_count, is_fever_mode, last_hit_time, fever_start_time

    game_mode = mode
    score = 0
    combo_count = 0
    is_fever_mode = False

    # 初始化計時器
    now = pygame.time.get_ticks()
    last_hit_time = now
    fever_start_time = 0

    current_level_idx = 0
    score_saved = False
    play_bgm(MUSIC_GAME)
    if mode == "LEVEL":
        setup_level(0)
    else:
        current_target = 0
        current_duration = 30
        mole_speed = 700
        mole_appear_rate = 600
        start_time = pygame.time.get_ticks()
        play_sfx(snd_start)
    game_state = "PLAYING"
    for h in hole_list: h.is_up = False


def setup_level(idx):
    global current_target, current_duration, mole_speed, mole_appear_rate, start_time, current_level_idx
    current_level_idx = idx
    if idx < len(LEVELS):
        cfg = LEVELS[idx]
        current_target = cfg['target']
        current_duration = cfg['time']
        mole_speed = cfg['speed']
        mole_appear_rate = cfg['appear']
    else:
        extra_level = idx - len(LEVELS) + 1
        base = LEVELS[-1]
        current_target = base['target'] + (extra_level * 120)
        current_duration = 40
        mole_speed = max(150, base['speed'] - (extra_level * 15))
        mole_appear_rate = max(100, base['appear'] - (extra_level * 5))
    start_time = pygame.time.get_ticks()
    play_sfx(snd_start)


# --- 主迴圈 ---
clock = pygame.time.Clock()
running = True


def draw_hammer_preview(surface, x, y, skin_id):
    skin = HAMMER_SKINS[skin_id]
    c_h = skin['c_handle']
    c_head = skin['c_head']
    c_d = skin['c_detail']
    pygame.draw.rect(surface, c_h, (x - 6, y, 12, 60), border_radius=3)
    pygame.draw.rect(surface, c_head, (x - 25, y - 15, 50, 30), border_radius=6)
    pygame.draw.rect(surface, c_d, (x - 22, y - 12, 44, 6), border_radius=3)


# 處理畫面震動的 Offset (加入震動開關判斷)
def get_shake_offset():
    global screen_shake
    if vibration_enabled and screen_shake > 0:
        screen_shake -= 1
        return random.randint(-4, 4), random.randint(-4, 4)
    return 0, 0


while running:
    # 1. 繪圖前置
    ox, oy = get_shake_offset()

    # 清除畫面，重新繪製
    SCREEN.fill((0, 0, 0))  # 黑底避免殘影
    game_surface = pygame.Surface((WIDTH, HEIGHT))  # 畫布

    btn_l, btn_e, btn_rank = None, None, None
    btn_p1, btn_p2 = None, None
    btn_rank_close = None
    pause_trigger = None
    btn_settings = None
    rect_mute_btn = None
    rect_vib_btn = None
    rect_bgm_slider = None
    rect_sfx_slider = None
    rect_settings_close = None
    btn_shop = None
    shop_skins_btns = None
    shop_close = None

    if game_state == "MENU":
        draw_background_scene(game_surface)
        draw_wood_board(game_surface)
        draw_text_with_outline(game_surface, "打地鼠 極致版", font_xl, TEXT_YELLOW, TEXT_OUTLINE, (WIDTH // 2, 80))
        draw_text_with_outline(game_surface, f"金幣: {user_data['coins']}", font_medium, (255, 200, 50), TEXT_OUTLINE,
                               (WIDTH // 2, 130))

        btn_l = pygame.Rect(WIDTH // 2 - 100, 280, 200, 70)
        draw_button_3d(game_surface, btn_l, "節奏闖關", (80, 160, 200))

        btn_e = pygame.Rect(WIDTH // 2 - 100, 370, 200, 70)
        draw_button_3d(game_surface, btn_e, "無盡模式", (200, 160, 80))

        btn_rank = pygame.Rect(WIDTH // 2 - 100, 460, 200, 70)
        draw_button_3d(game_surface, btn_rank, "歷史排行", (150, 100, 200))

        btn_settings = draw_settings_icon(game_surface, WIDTH - 80, HEIGHT - 80)
        btn_shop = draw_shop_button(game_surface, 20, HEIGHT - 80)

    elif game_state == "SETTINGS":
        draw_background_scene(game_surface)
        draw_wood_board(game_surface)
        draw_text_with_outline(game_surface, "設定", font_xl, TEXT_YELLOW, TEXT_OUTLINE, (WIDTH // 2, 80))
        # 接收震動按鈕的 rect
        rect_mute_btn, rect_vib_btn, rect_bgm_slider, rect_sfx_slider, rect_settings_close = draw_settings_window(
            game_surface)

    elif game_state == "SHOP":
        draw_background_scene(game_surface)
        draw_wood_board(game_surface)
        draw_text_with_outline(game_surface, "商店", font_xl, TEXT_YELLOW, TEXT_OUTLINE, (WIDTH // 2, 80))
        shop_skins_btns, shop_close = draw_shop_window(game_surface)

    elif game_state == "PLAYING":
        draw_background_scene(game_surface)  # 1. 背景

        hole_list.sort(key=lambda h: h.rect.y)
        for h in hole_list: h.draw(game_surface)  # 2. 地鼠與坑洞

        for ft in floating_texts: ft.draw(game_surface)  # 3. 飄浮文字
        for burst in hit_effects: burst.draw(game_surface)  # 4. 打擊特效

        pause_trigger = draw_hud_ui(game_surface)  # 5. 上方 HUD

        draw_combo_ui(game_surface)  # 6. 下方 Combo UI (最上層)

    elif game_state == "PAUSED":
        draw_background_scene(game_surface)
        hole_list.sort(key=lambda h: h.rect.y)
        for h in hole_list: h.draw(game_surface)
        draw_hud_ui(game_surface)
        btn_p1, btn_p2 = draw_popup(game_surface, "遊戲暫停", "休息一下聽音樂~", "繼續", "回選單")

    elif game_state == "LEVEL_CLEAR":
        draw_background_scene(game_surface)
        hole_list.sort(key=lambda h: h.rect.y)
        for h in hole_list: h.draw(game_surface)
        draw_hud_ui(game_surface)
        next_lv = current_level_idx + 2
        btn_p1, btn_p2 = draw_popup(game_surface, "關卡完成!", f"得分: {int(score)}", f"前進第 {next_lv} 關", "回選單")

    elif game_state == "GAME_OVER":
        draw_background_scene(game_surface)
        hole_list.sort(key=lambda h: h.rect.y)
        for h in hole_list: h.draw(game_surface)
        draw_hud_ui(game_surface)
        msg = "挑戰失敗!" if game_mode == "LEVEL" and score < current_target else f"最終得分: {int(score)}"
        if game_mode == "ENDLESS" and not score_saved:
            save_to_leaderboard(int(score))
            score_saved = True
        btn_p1, btn_p2 = draw_popup(game_surface, "遊戲結束", msg, "重試", "回選單")

    elif game_state == "SHOW_RANKING":
        draw_background_scene(game_surface)
        draw_wood_board(game_surface)
        draw_text_with_outline(game_surface, "排行榜", font_xl, TEXT_YELLOW, TEXT_OUTLINE, (WIDTH // 2, 80))
        btn_rank_close = draw_leaderboard_popup(game_surface)

    # 繪製 Hammer
    mx, my = pygame.mouse.get_pos()
    pygame.mouse.set_visible(False)
    hammer.update()
    hammer.draw(game_surface, mx, my)

    # 將畫布繪製到螢幕 (帶有震動偏移)
    SCREEN.blit(game_surface, (ox, oy))
    pygame.display.flip()

    # 2. 事件
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            save_userdata()

        if game_state == "SETTINGS":
            if event.type == pygame.MOUSEBUTTONDOWN or (event.type == pygame.MOUSEMOTION and event.buttons[0]):
                if rect_bgm_slider and rect_bgm_slider.collidepoint(mx - ox, my - oy):
                    ratio = (mx - ox - rect_bgm_slider.x) / rect_bgm_slider.width
                    vol_bgm_level = max(0.0, min(1.0, ratio))
                    update_bgm_volume()
                if rect_sfx_slider and rect_sfx_slider.collidepoint(mx - ox, my - oy):
                    ratio = (mx - ox - rect_sfx_slider.x) / rect_sfx_slider.width
                    vol_sfx_level = max(0.0, min(1.0, ratio))
                    update_sfx_volume()
                    if event.type == pygame.MOUSEBUTTONDOWN: play_sfx(snd_hit)

        if event.type == pygame.MOUSEBUTTONDOWN:
            hammer.swing()  # 揮動槌子
            r_mx, r_my = mx - ox, my - oy  # 修正點擊座標

            if game_state == "MENU":
                if btn_l and btn_l.collidepoint((r_mx, r_my)): start_game("LEVEL")
                if btn_e and btn_e.collidepoint((r_mx, r_my)): start_game("ENDLESS")
                if btn_rank and btn_rank.collidepoint((r_mx, r_my)):
                    game_state = "SHOW_RANKING"
                if btn_settings and btn_settings.collidepoint((r_mx, r_my)):
                    game_state = "SETTINGS"
                if btn_shop and btn_shop.collidepoint((r_mx, r_my)):
                    game_state = "SHOP"

            elif game_state == "SHOP":
                if shop_close and shop_close.collidepoint((r_mx, r_my)):
                    game_state = "MENU"
                    save_userdata()
                if shop_skins_btns:
                    for skin_id, rect in shop_skins_btns.items():
                        if rect.collidepoint((r_mx, r_my)):
                            info = HAMMER_SKINS[skin_id]
                            if skin_id in user_data['owned_skins']:
                                user_data['current_skin'] = skin_id
                                play_sfx(snd_hit)
                            else:
                                if user_data['coins'] >= info['price']:
                                    user_data['coins'] -= info['price']
                                    user_data['owned_skins'].append(skin_id)
                                    user_data['current_skin'] = skin_id
                                    play_sfx(snd_coin)
                                else:
                                    play_sfx(snd_lose)

            elif game_state == "SETTINGS":
                if rect_mute_btn and rect_mute_btn.collidepoint((r_mx, r_my)):
                    toggle_music_enabled(not sound_enabled)
                # ★★★ 震動開關事件 ★★★
                if rect_vib_btn and rect_vib_btn.collidepoint((r_mx, r_my)):
                    vibration_enabled = not vibration_enabled
                if rect_settings_close and rect_settings_close.collidepoint((r_mx, r_my)):
                    game_state = "MENU"

            elif game_state == "SHOW_RANKING":
                if btn_rank_close and btn_rank_close.collidepoint((r_mx, r_my)):
                    game_state = "MENU"

            elif game_state == "PLAYING":
                if pause_trigger and pause_trigger.collidepoint((r_mx, r_my)):
                    game_state = "PAUSED"
                    pause_start_time = pygame.time.get_ticks()
                    pygame.mixer.music.pause()
                else:
                    # ★★★ 核心判斷：是否打中地鼠？ ★★★
                    hit_something = False
                    # 反向檢查，優先點擊下層的地鼠（如果重疊）
                    for h in reversed(hole_list):
                        if h.check_click((r_mx, r_my)):
                            hit_something = True

                            # 更新最後打擊時間
                            last_hit_time = pygame.time.get_ticks()

                            # --- Combo 邏輯 ---
                            combo_count += 1
                            if combo_count == 10:  # 啟動 Fever
                                is_fever_mode = True
                                fever_start_time = pygame.time.get_ticks()  # 記錄 Fever 開始時間
                                play_sfx(snd_fever)

                            # 分數計算 (Combo 加成)
                            s_val = h.get_score()
                            multiplier = 2 if is_fever_mode else 1
                            combo_bonus = int(combo_count * 0.5)  # 稍微增加 Combo 加分感
                            total_score = (s_val * multiplier) + combo_bonus
                            score += total_score

                            # 特效
                            hit_effects.append(HitBurst(r_mx, r_my, is_combo=(combo_count > 1)))

                            # 顯示的數字也加上 Combo 文字
                            txt_show = f"+{int(total_score)}"
                            if combo_count > 1: txt_show += "!"
                            floating_texts.append(
                                FloatingText(r_mx, r_my, txt_show, size="large" if is_fever_mode else "medium"))

                            # 震動 (受 vibration_enabled 控制)
                            if s_val >= 3 or is_fever_mode:
                                screen_shake = 10
                            else:
                                screen_shake = 3

                            if s_val == 3:
                                play_sfx(snd_hit_gold)
                            elif s_val == 2:
                                play_sfx(snd_hit_silver)
                            else:
                                play_sfx(snd_hit)

                            if random.random() < 0.3:
                                gain = random.randint(1, 3) * multiplier
                                user_data['coins'] += gain
                                play_sfx(snd_coin)
                                floating_texts.append(FloatingText(r_mx, r_my - 40, f"+${gain}", (255, 200, 50)))
                            break

                    # --- 揮空懲罰 (修改邏輯) ---
                    if not hit_something:
                        if is_fever_mode:
                            # Fever 模式：揮空不懲罰
                            pass
                        else:
                            # 一般模式：揮空重置連擊
                            if combo_count > 0:
                                floating_texts.append(FloatingText(r_mx, r_my, "MISS", (200, 200, 200)))
                            combo_count = 0

            elif game_state == "PAUSED":
                if btn_p1 and btn_p1.collidepoint((r_mx, r_my)):
                    duration = pygame.time.get_ticks() - pause_start_time
                    start_time += duration
                    last_hit_time += duration  # 暫停時不計算連擊時間
                    if is_fever_mode: fever_start_time += duration  # 暫停不扣 Fever 時間
                    for h in hole_list:
                        if h.is_up: h.up_start_time += duration
                    game_state = "PLAYING"
                    if sound_enabled: pygame.mixer.music.unpause()
                if btn_p2 and btn_p2.collidepoint((r_mx, r_my)):
                    game_state = "MENU"
                    play_bgm(MUSIC_MENU)
                    save_userdata()

            elif game_state == "LEVEL_CLEAR":
                if btn_p1 and btn_p1.collidepoint((r_mx, r_my)):
                    setup_level(current_level_idx + 1)
                    game_state = "PLAYING"
                    combo_count = 0
                    is_fever_mode = False
                if btn_p2 and btn_p2.collidepoint((r_mx, r_my)):
                    game_state = "MENU"
                    play_bgm(MUSIC_MENU)
                    save_userdata()

            elif game_state == "GAME_OVER":
                if btn_p1 and btn_p1.collidepoint((r_mx, r_my)):
                    start_game(game_mode)
                if btn_p2 and btn_p2.collidepoint((r_mx, r_my)):
                    game_state = "MENU"
                    play_bgm(MUSIC_MENU)
                    save_userdata()

        if event.type == pygame.MOUSEBUTTONUP:
            hammer.reset()

    # 3. 邏輯更新
    if game_state == "PLAYING":
        elapsed = (pygame.time.get_ticks() - start_time) // 1000
        if elapsed >= current_duration:
            if game_mode == "LEVEL":
                if score >= current_target:
                    game_state = "LEVEL_CLEAR"
                    play_sfx(snd_win)
                else:
                    game_state = "GAME_OVER"
                    play_sfx(snd_lose)
            else:
                game_state = "GAME_OVER"
                play_sfx(snd_lose)

        now = pygame.time.get_ticks()

        # --- 連擊與 Fever 倒數計時邏輯 ---
        if is_fever_mode:
            # 檢查 Fever 是否持續超過 10 秒
            if now - fever_start_time > 10000:
                is_fever_mode = False
                combo_count = 0  # 重置連擊
                floating_texts.append(FloatingText(WIDTH // 2, HEIGHT // 2, "Fever End", (200, 200, 200), size="large"))
        else:
            # 檢查是否超過 5 秒沒打擊
            if combo_count > 0 and (now - last_hit_time > 5000):
                combo_count = 0
                floating_texts.append(FloatingText(WIDTH // 2, HEIGHT // 2, "Combo Lost", (200, 200, 200)))

        appear_time = mole_appear_rate
        stay_time = mole_speed

        # Fever 模式加速地鼠出現
        if is_fever_mode:
            appear_time = max(150, appear_time * 0.6)
            stay_time = max(200, stay_time * 0.8)

        if game_mode == "ENDLESS":
            appear_time = max(200, 600 - score * 5)
            stay_time = max(300, 800 - score * 5)

        if now - last_mole_time > appear_time:
            avail = [h for h in hole_list if not h.is_up]
            if avail:
                h = random.choice(avail)
                h.pop_up(stay_time)
                last_mole_time = now

        for h in hole_list: h.update()
        floating_texts = [ft for ft in floating_texts if ft.update()]
        hit_effects = [he for he in hit_effects if he.update()]

    clock.tick(FPS)

pygame.quit()
