# main.py — 3-Weapon System + Enemy hierarchy
import pygame
import sys
import math
import random
from config import *
from player import Player
from entities import Enemy, RangedEnemy, Boss, ExpGem, EnemyBullet, FastEnemy, TankEnemy
from spells import SpellManager
from runes import CoreRune, SplitRune, BounceRune, SpiralRune, HeavyBurdenRune, HeavyHitterRune, SelfCenteredRune
from status_effect import StatusEffect
from weapons import FireWeapon, IceWeapon, LightningWeapon, WindWeapon

# ═══════════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════════
def draw_grid(screen, cx, cy):
    GRID_SIZE = 60
    sx, sy = -(cx % GRID_SIZE), -(cy % GRID_SIZE)
    for x in range(int(sx), WIDTH, GRID_SIZE):
        pygame.draw.line(screen, (30, 30, 30), (x, 0), (x, HEIGHT))
    for y in range(int(sy), HEIGHT, GRID_SIZE):
        pygame.draw.line(screen, (30, 30, 30), (0, y), (WIDTH, y))

def update_tree_layout(core, start_x, start_y):
    # Core is a CoreRune instance
    for slot in core.slots:
        sx, sy = start_x + slot['rel_x'], start_y + slot['rel_y']
        if slot['rune']:
            if not slot['rune'].is_dragging:
                slot['rune'].ui_x, slot['rune'].ui_y = sx, sy
        # Store slot UI position for reference
        slot['ui_x'], slot['ui_y'] = sx, sy

def draw_connections(screen, core):
    for slot in core.slots:
        if slot['parent_id'] != -1:
            p_slot = core.slots[slot['parent_id']]
            # Draw a line between slot positions
            color = (100, 100, 100) if not slot['rune'] else (255, 165, 0)
            pygame.draw.line(screen, color, (p_slot['ui_x'], p_slot['ui_y']), (slot['ui_x'], slot['ui_y']), 2)
            
def draw_slots(screen, core, font):
    for slot in core.slots:
        # Draw a faint circle for empty slots
        if not slot['rune']:
            pygame.draw.circle(screen, (50, 50, 50), (slot['ui_x'], slot['ui_y']), 25, 2)
            # Maybe a small dot in center
            pygame.draw.circle(screen, (70, 70, 70), (slot['ui_x'], slot['ui_y']), 4)

def get_all_nodes(core):
    nodes = []
    for s in core.slots:
        if s['rune']: nodes.append(s['rune'])
    return nodes

def get_random_rune():
    return random.choice([SplitRune, BounceRune, SpiralRune, HeavyBurdenRune, HeavyHitterRune, SelfCenteredRune])()

def random_spawn_pos(px, py, radius=600):
    angle = random.uniform(0, 2 * math.pi)
    return px + math.cos(angle) * radius, py + math.sin(angle) * radius

# ═══════════════════════════════════════════════════════════════
#  WEAPON SELECT SCREEN
# ═══════════════════════════════════════════════════════════════
WEAPON_CARDS = [
    {
        "key":   "fire",
        "name":  "FIRE",
        "sub":   "Pyromancer",
        "desc":  ["Click to shoot fireballs", "Burns enemies over time", "Fast fire rate"],
        "color": (200, 60, 10),
        "glow":  (255, 140, 40),
        "dark":  (80, 15, 0),
    },
    {
        "key":   "ice",
        "name":  "ICE",
        "sub":   "Cryomancer",
        "desc":  ["Hold to charge", "Longer hold = bigger shot", "Slows enemies 70%"],
        "color": (30, 140, 220),
        "glow":  (120, 210, 255),
        "dark":  (0, 30, 80),
    },
    {
        "key":   "lightning",
        "name":  "LIGHTNING",
        "sub":   "Stormcaller",
        "desc":  ["Hold to zap continuously", "Chains to 2 nearby enemies", "Overload: speed boost + sparks"],
        "color": (180, 160, 0),
        "glow":  (255, 255, 80),
        "dark":  (40, 35, 0),
    },
    {
        "key":   "wind",
        "name":  "WIND",
        "sub":   "Aeromancer",
        "desc":  ["Fixed range boomerang", "Pierces all enemies", "Deals damage twice"],
        "color": (60, 200, 100),
        "glow":  (150, 255, 180),
        "dark":  (5, 40, 15),
    },
]

def draw_weapon_select(screen, font, font_large, mouse_pos, t):
    screen.fill((8, 8, 18))
    # Stars background
    random.seed(42)
    for _ in range(80):
        rx, ry = random.randint(0, WIDTH), random.randint(0, HEIGHT)
        br = int(100 + 80 * math.sin(t * 2 + rx * 0.05))
        pygame.draw.circle(screen, (br, br, br), (rx, ry), 1)
    random.seed()

    title = font_large.render("CHOOSE YOUR WEAPON", True, (220, 220, 255))
    screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 38))

    hint = font.render("Click a card to select", True, (120, 120, 160))
    screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, 80))

    card_w, card_h = 175, 270
    gap = 20
    total = 4 * card_w + 3 * gap
    start_x = (WIDTH - total) // 2
    start_y = 120

    hovered = -1
    for i, card in enumerate(WEAPON_CARDS):
        cx = start_x + i * (card_w + gap)
        rect = pygame.Rect(cx, start_y, card_w, card_h)
        if rect.collidepoint(mouse_pos):
            hovered = i

    for i, card in enumerate(WEAPON_CARDS):
        cx = start_x + i * (card_w + gap)
        rect = pygame.Rect(cx, start_y, card_w, card_h)
        is_hov = (hovered == i)

        # Shadow
        shadow = pygame.Surface((card_w + 10, card_h + 10), pygame.SRCALPHA)
        pygame.draw.rect(shadow, (0, 0, 0, 100), (5, 5, card_w, card_h), border_radius=14)
        screen.blit(shadow, (cx - 3, start_y - 3))

        # Card background — draw directly on screen to avoid SRCALPHA+border_radius bug
        pulse = int(15 * math.sin(t * 3 + i * 1.2)) if is_hov else 0
        dr = max(0, min(255, card["dark"][0] + pulse))
        dg = max(0, min(255, card["dark"][1] + pulse))
        db = max(0, min(255, card["dark"][2] + pulse))
        pygame.draw.rect(screen, (dr, dg, db), (cx, start_y, card_w, card_h), border_radius=12)

        # Glow border
        brd_color = card["glow"] if is_hov else card["color"]
        brd_w = 3 if is_hov else 2
        pygame.draw.rect(screen, brd_color, (cx, start_y, card_w, card_h), brd_w, border_radius=12)


        # Icon area gradient strip
        icon_surf = pygame.Surface((card_w, 90), pygame.SRCALPHA)
        cr, cg, cb = card["color"][0], card["color"][1], card["color"][2]
        for row in range(90):
            a = int(180 * (1 - row / 90))
            pygame.draw.line(icon_surf, (cr, cg, cb, a), (0, row), (card_w, row))
        screen.blit(icon_surf, (cx, start_y))

        # Icon shape
        ic_cx, ic_cy = cx + card_w // 2, start_y + 45
        if card["key"] == "fire":
            for r in range(22, 0, -4):
                fade = int(255 * r / 22)
                pygame.draw.circle(screen, (fade, int(fade * 0.35), 0), (ic_cx, ic_cy), r)
        elif card["key"] == "ice":
            for r in range(22, 0, -4):
                c_val = int(80 + 175 * r / 22)
                pygame.draw.circle(screen, (0, int(c_val * 0.6), c_val), (ic_cx, ic_cy), r)
            for ang in range(0, 360, 60):
                rad = math.radians(ang)
                ex = ic_cx + int(22 * math.cos(rad))
                ey = ic_cy + int(22 * math.sin(rad))
                pygame.draw.line(screen, (180, 230, 255), (ic_cx, ic_cy), (ex, ey), 2)
        elif card["key"] == "lightning":
            pts = [(ic_cx-6, ic_cy-22), (ic_cx+2, ic_cy-4),
                   (ic_cx+8, ic_cy-4), (ic_cx-4, ic_cy+22),
                   (ic_cx+0, ic_cy+4),  (ic_cx-8, ic_cy+4)]
            pygame.draw.polygon(screen, (255, 255, 80), pts)
            pygame.draw.polygon(screen, (255, 230, 0), pts, 2)
        elif card["key"] == "wind":
            for r in range(22, 5, -6):
                pygame.draw.circle(screen, (100, 255, 150), (ic_cx, ic_cy), r, 2)
                # Small blades
                for ang in range(0, 360, 120):
                    rad = math.radians(ang + t * 400)
                    bx = ic_cx + math.cos(rad) * r
                    by = ic_cy + math.sin(rad) * r
                    pygame.draw.line(screen, (200, 255, 200), (ic_cx, ic_cy), (bx, by), 2)

        # Name
        name_s = font_large.render(card["name"], True, card["glow"])
        screen.blit(name_s, (cx + card_w // 2 - name_s.get_width() // 2, start_y + 96))

        sub_s = font.render(card["sub"], True, card["color"])
        screen.blit(sub_s, (cx + card_w // 2 - sub_s.get_width() // 2, start_y + 126))

        # Divider
        pygame.draw.line(screen, card["color"],
                         (cx + 16, start_y + 148), (cx + card_w - 16, start_y + 148), 1)

        # Desc lines
        for j, line in enumerate(card["desc"]):
            col = card["glow"] if is_hov else (180, 180, 200)
            txt = font.render(f"• {line}", True, col)
            screen.blit(txt, (cx + 10, start_y + 158 + j * 22))

        # Hover highlight bottom
        if is_hov:
            br, bg, bb = card["color"][0], card["color"][1], card["color"][2]
            pygame.draw.rect(screen, (br, bg, bb),
                             (cx + 10, start_y + card_h - 36, card_w - 20, 28), border_radius=6)
            sel = font.render("SELECT", True, WHITE)
            screen.blit(sel, (cx + card_w // 2 - sel.get_width() // 2, start_y + card_h - 30))

    return hovered

# ═══════════════════════════════════════════════════════════════
#  STATS PANEL (New)
# ═══════════════════════════════════════════════════════════════
def draw_stats_panel(screen, font, font_l, weapon_type):
    data = {
        "fire": {
            "name": "FURI IGNI",
            "desc": "A short-ranged punch of fire.",
            "stats": [("Damage", "50"), ("Duration", "0.1s"), ("Size", "1.5"), ("Apply 1", "Burn", (255, 100, 20))],
            "keyword": ("Burn", "Deals stacking damage over time.", (255, 100, 20)),
            "color": (255, 100, 20)
        },
        "ice": {
            "name": "NOSTA AQUA",
            "desc": "Shards of ice, that can be charged to hit foes from a great distance.",
            "stats": [("Damage", "0 <=> 250"), ("Duration", "0.0s <=> 0.4s"), ("Speed", "40"), ("Apply 25", "Chill", (100, 200, 255))],
            "extra": "The longer the charge, the greater its damage and range",
            "keyword": ("Chill/Freeze", "Builds up to slow foes until they are completely frozen.", (100, 200, 255)),
            "color": (80, 200, 255)
        },
        "lightning": {
            "name": "EXAE AURA",
            "desc": "A dangerous beam of lightning.",
            "stats": [("Damage", "40"), ("Duration", "2.0s"), ("Length", "12"), ("Apply 20", "Static", (255, 255, 60))],
            "extra": "Overflows after prolonged use, requires a cooldown period before it can be used again",
            "keyword": ("Static", "Builds up until it casts a chain of lightning at nearby foes.", (255, 255, 60)),
            "color": (255, 255, 60)
        },
        "wind": {
            "name": "CELE AER",
            "desc": "A boomerang that returns when called back.",
            "stats": [("Damage", "60"), ("Duration", "0.24s"), ("Speed", "30"), ("", "Pierce", (100, 255, 150), "2")],
            "extra": "Must return before it can be cast again",
            "keyword": ("Pierce", "Passes through targets.", (100, 255, 150)),
            "color": (100, 255, 150)
        }
    }
    
    info = data.get(weapon_type)
    if not info: return
    
    px, py = 20, 100
    pw, ph = 280, 400
    
    # Background
    bg_surf = pygame.Surface((pw, ph), pygame.SRCALPHA)
    pygame.draw.rect(bg_surf, (10, 10, 25, 220), (0, 0, pw, ph), border_radius=10)
    pygame.draw.rect(bg_surf, info["color"], (0, 0, pw, ph), 2, border_radius=10)
    screen.blit(bg_surf, (px, py))
    
    # Header
    name_s = font_l.render(info["name"], True, info["color"])
    screen.blit(name_s, (px + pw//2 - name_s.get_width()//2, py + 20))
    
    # Description (wrap text)
    y_off = py + 60
    words = info["desc"].split()
    line = ""
    for w in words:
        if font.size(line + w)[0] < pw - 40:
            line += w + " "
        else:
            txt = font.render(line, True, (220, 220, 220))
            screen.blit(txt, (px + 20, y_off))
            y_off += 20; line = w + " "
    screen.blit(font.render(line, True, (220, 220, 220)), (px + 20, y_off))
    y_off += 30
    
    # Stats
    for s in info["stats"]:
        # Bullet diamond
        pygame.draw.polygon(screen, info["color"], [(px+20, y_off+8), (px+24, y_off+4), (px+28, y_off+8), (px+24, y_off+12)])
        label = font.render(f"  {s[0]}: ", True, WHITE)
        screen.blit(label, (px + 20, y_off))
        val_x = px + 20 + label.get_width()
        if len(s) >= 3: # With colored keyword
            val = font.render(s[1], True, WHITE)
            screen.blit(val, (val_x, y_off))
            kw = font.render(f" {s[2]}", True, s[2] if isinstance(s[2], tuple) else info["color"])
            screen.blit(kw, (val_x + val.get_width(), y_off))
            if len(s) == 4: # Extra value after keyword
                screen.blit(font.render(f" {s[3]}", True, WHITE), (val_x + val.get_width() + kw.get_width(), y_off))
        else:
            val = font.render(s[1], True, (255, 255, 255))
            screen.blit(val, (val_x, y_off))
        y_off += 25
        
    if "extra" in info:
        words = info["extra"].split()
        line = ""
        pygame.draw.polygon(screen, info["color"], [(px+20, y_off+8), (px+24, y_off+4), (px+28, y_off+8), (px+24, y_off+12)])
        y_off_start = y_off
        for w in words:
            if font.size("   " + line + w)[0] < pw - 40:
                line += w + " "
            else:
                screen.blit(font.render("   " + line, True, (220, 220, 220)), (px + 20, y_off))
                y_off += 20; line = w + " "
        screen.blit(font.render("   " + line, True, (220, 220, 220)), (px + 20, y_off))
        y_off += 40

    # Keyword Box
    kw_bg = pygame.Surface((pw - 20, 80), pygame.SRCALPHA)
    pygame.draw.rect(kw_bg, (5, 5, 15, 200), (0, 0, pw - 20, 80), border_radius=5)
    pygame.draw.rect(kw_bg, info["keyword"][2], (0, 0, pw - 20, 80), 1, border_radius=5)
    screen.blit(kw_bg, (px + 10, py + ph - 90))
    
    kw_name = font.render(info["keyword"][0], True, info["keyword"][2])
    screen.blit(kw_name, (px + 20, py + ph - 80))
    
    kw_desc = info["keyword"][1]
    words = kw_desc.split()
    line = ""; d_off = py + ph - 60
    for w in words:
        if font.size(line + w)[0] < pw - 40:
            line += w + " "
        else:
            screen.blit(font.render(line, True, WHITE), (px + 20, d_off))
            d_off += 18; line = w + " "
    screen.blit(font.render(line, True, WHITE), (px + 20, d_off))

# ═══════════════════════════════════════════════════════════════
#  LEVEL UP SELECT SCREEN (New)
# ═══════════════════════════════════════════════════════════════
def draw_level_up_select(screen, font, font_l, options):
    # Overlay
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))
    
    title = font_l.render("SELECT A MEMORY", True, WHITE)
    screen.blit(title, (WIDTH//2 - title.get_width()//2, 50))
    
    mx, my = pygame.mouse.get_pos()
    hovered_idx = -1
    
    cw, ch = 260, 340
    gap = 40
    total_w = 3 * cw + 2 * gap
    start_x = (WIDTH - total_w) // 2
    start_y = 200
    
    for i, rune in enumerate(options):
        rx = start_x + i * (cw + gap)
        ry = start_y
        rect = pygame.Rect(rx, ry, cw, ch)
        
        is_hover = rect.collidepoint(mx, my)
        if is_hover: hovered_idx = i
        
        # Draw Card
        color = (30, 30, 50, 220) if not is_hover else (50, 50, 80, 240)
        card_surf = pygame.Surface((cw, ch), pygame.SRCALPHA)
        pygame.draw.rect(card_surf, color, (0, 0, cw, ch), border_radius=15)
        pygame.draw.rect(card_surf, WHITE if not is_hover else YELLOW, (0, 0, cw, ch), 2, border_radius=15)
        screen.blit(card_surf, (rx, ry))
        
        # Rune Icon/Name
        name_s = font_l.render(rune.name.upper(), True, YELLOW if rune.cost > 1 else WHITE)
        screen.blit(name_s, (rx + cw//2 - name_s.get_width()//2, ry + 30))
        
        rarity = "Rare Modifier" if rune.cost > 1 else "Common Modifier"
        rarity_s = font.render(rarity, True, (180, 180, 200))
        screen.blit(rarity_s, (rx + cw//2 - rarity_s.get_width()//2, ry + 60))
        
        # Stats based on type
        y_off = ry + 120
        stats = []
        if isinstance(rune, HeavyBurdenRune):
            stats = [("Damage", "+15%"), ("Size", "+20%")]
        elif isinstance(rune, HeavyHitterRune):
            stats = [("Damage", "+50%"), ("Speed", "-25%")]
        elif isinstance(rune, SelfCenteredRune):
            stats = [("Add Orbit movement", ""), ("Spawn Count", "+1"), ("Duration", "+80%")]
        elif isinstance(rune, SplitRune):
            stats = [("Projectiles", "Split")]
        elif isinstance(rune, BounceRune):
            stats = [("Bounce Count", "2")]
        elif isinstance(rune, SpiralRune):
            stats = [("Movement", "Spiral")]
            
        for s_label, s_val in stats:
            pygame.draw.polygon(screen, YELLOW, [(rx+20, y_off+8), (rx+24, y_off+4), (rx+28, y_off+8), (rx+24, y_off+12)])
            txt = font.render(f"  {s_label} ", True, WHITE)
            screen.blit(txt, (rx + 20, y_off))
            val = font.render(s_val, True, YELLOW)
            screen.blit(val, (rx + 20 + txt.get_width(), y_off))
            y_off += 30

    return hovered_idx

# ═══════════════════════════════════════════════════════════════
#  HUD
# ═══════════════════════════════════════════════════════════════
def draw_hud(screen, player, boss, wave_num, font, font_large):
    # HP Bar
    pygame.draw.rect(screen, (60, 0, 0),     (10, HEIGHT - 62, 200, 18))
    pygame.draw.rect(screen, (200, 40, 40),  (10, HEIGHT - 62, int(200 * player.get_hp_ratio()), 18))
    pygame.draw.rect(screen, WHITE,          (10, HEIGHT - 62, 200, 18), 2)
    screen.blit(font.render(f"HP {int(player.hp)}/{player.max_hp}", True, WHITE), (14, HEIGHT - 60))

    # XP Bar
    pygame.draw.rect(screen, (0, 30, 70),    (10, HEIGHT - 38, 200, 10))
    pygame.draw.rect(screen, (50, 150, 255), (10, HEIGHT - 38, int(200 * player.get_xp_ratio()), 10))
    pygame.draw.rect(screen, WHITE,          (10, HEIGHT - 38, 200, 10), 1)
    screen.blit(font.render(f"XP {player.exp}/{player.max_exp}", True, WHITE), (14, HEIGHT - 39))

    # Wave/Level
    screen.blit(font_large.render(f"LVL {player.level}  Wave {wave_num}  [TAB] Rune", True, WHITE), (10, 10))

    # Weapon HUD
    if player.weapon:
        wname = {"fire": "FIRE", "ice": "ICE", "lightning": "LIGHTNING", "wind": "WIND"}.get(player.weapon_type, "")
        wcol  = {"fire": (255,100,20), "ice": (80,200,255), "lightning": (255,255,60), "wind": (100,255,150)}.get(player.weapon_type, WHITE)
        screen.blit(font.render(f"[{wname}]", True, wcol), (WIDTH - 140, 10))
        player.weapon.draw_hud(screen, font, WIDTH - 160, 32)

    # Boss HP Bar
    if boss and boss.alive:
        bw = 400
        bx = WIDTH // 2 - bw // 2
        pygame.draw.rect(screen, (60, 0, 60),   (bx, HEIGHT - 94, bw, 20))
        pygame.draw.rect(screen, (220, 0, 220), (bx, HEIGHT - 94, int(bw * boss.get_hp_ratio()), 20))
        pygame.draw.rect(screen, WHITE,         (bx, HEIGHT - 94, bw, 20), 2)
        bl = font.render(f"BOSS  {int(boss.hp)}/{boss.max_hp}", True, WHITE)
        screen.blit(bl, (bx + bw // 2 - bl.get_width() // 2, HEIGHT - 92))

# ═══════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Runic Survivor — Weapon Select")
    clock  = pygame.time.Clock()
    font   = pygame.font.SysFont(None, 24)
    font_l = pygame.font.SysFont(None, 40)

    player = Player(WIDTH // 2, HEIGHT // 2)
    player.spell_manager = SpellManager(player)
    player.spell_manager.core_tree = CoreRune("Fire", 5)

    inventory, enemies, gems, enemy_bullets, weapon_projectiles = [], [], [], [], []
    boss = None

    spawn_timer  = 0.0
    SPAWN_INT    = 2.5
    wave_num     = 0
    BOSS_WAVE    = 5
    player_ihit  = 0.0   # invincibility timer
    HIT_CD       = 0.8

    game_state   = "WEAPON_SELECT"
    dragged_rune = None
    hovered_card = -1
    hovered_lvl_up = -1
    level_up_options = []
    t_anim       = 0.0   # animation timer for select screen

    wave_notif_timer = 0.0
    wave_notif_text = ""

    # Mouse state tracking
    mouse_held      = False
    just_released   = False
    hovered_card    = -1

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        t_anim += dt
        mouse_pos = pygame.mouse.get_pos()
        just_released = False

        # ── EVENTS ────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_TAB and game_state == "PLAYING":
                    game_state = "RUNE_MENU"
                    dragged_rune = None
                elif event.key == pygame.K_TAB and game_state == "RUNE_MENU":
                    game_state = "PLAYING"
                elif event.key == pygame.K_r and game_state == "GAME_OVER":
                    main(); return
                    
                # ===== THÊM ĐOẠN NÀY ĐỂ HACK RUNE =====
                elif event.key == pygame.K_F1:
                    inventory.extend([
                        SplitRune(), 
                        BounceRune(), 
                        SpiralRune(), 
                        HeavyBurdenRune(), 
                        HeavyHitterRune(), 
                        SelfCenteredRune()
                    ])
                    print("Đã hack thành công 1 bộ Rune vào túi đồ!")
                # ======================================
            # ===== ĐỔI VŨ KHÍ NHANH BẰNG PHÍM 1, 2, 3, 4 =====
                elif event.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4] and game_state == "PLAYING":
                    # 1. Thu hồi toàn bộ Rune trên Core cũ về Inventory để không bị mất
                    old_core = player.spell_manager.core_tree
                    for slot in old_core.slots:
                        rune = slot['rune']
                        # Bỏ qua chính bản thân cái Core
                        if rune and rune != old_core:
                            old_core.remove_rune(rune)
                            if rune not in inventory:
                                inventory.append(rune)
                    
                    # 2. Đổi vũ khí và Lõi tương ứng
                    if event.key == pygame.K_1:
                        player.weapon_type = "fire"
                        player.weapon = FireWeapon(player.damage)
                        player.spell_manager.core_tree = CoreRune("Fire", 5)
                    elif event.key == pygame.K_2:
                        player.weapon_type = "ice"
                        player.weapon = IceWeapon(player.damage)
                        player.spell_manager.core_tree = CoreRune("Ice", 5)
                    elif event.key == pygame.K_3:
                        player.weapon_type = "lightning"
                        player.weapon = LightningWeapon(player.damage)
                        player.spell_manager.core_tree = CoreRune("Lightning", 5)
                    elif event.key == pygame.K_4:
                        player.weapon_type = "wind"
                        player.weapon = WindWeapon(player.damage)
                        player.spell_manager.core_tree = CoreRune("Wind", 5)
                        
                    print(f"Đã chuyển sang vũ khí: {player.weapon_type.upper()}")
                # =================================================
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_held = True
                if game_state == "WEAPON_SELECT":
                    if hovered_card >= 0:
                        key = WEAPON_CARDS[hovered_card]["key"]
                        player.weapon_type = key
                        if key == "fire":
                            player.weapon = FireWeapon(player.damage)
                            player.spell_manager.core_tree = CoreRune("Fire", 5)
                        elif key == "ice":
                            player.weapon = IceWeapon(player.damage)
                            player.spell_manager.core_tree = CoreRune("Ice", 5)
                        elif key == "wind":
                            player.weapon = WindWeapon(player.damage)
                            player.spell_manager.core_tree = CoreRune("Wind", 5)
                        else:
                            player.weapon = LightningWeapon(player.damage)
                            player.spell_manager.core_tree = CoreRune("Lightning", 5)
                        game_state = "PLAYING"

                elif game_state == "LEVEL_UP_SELECT":
                    if hovered_lvl_up >= 0:
                        inventory.append(level_up_options[hovered_lvl_up])
                        level_up_options = []
                        game_state = "PLAYING"

                elif game_state == "RUNE_MENU":
                    mx, my = mouse_pos
                    for rune in inventory:
                        if math.hypot(mx - rune.ui_x, my - rune.ui_y) <= rune.ui_radius:
                            dragged_rune = rune; rune.is_dragging = True; break
                    if not dragged_rune:
                        core = player.spell_manager.core_tree
                        for rune in get_all_nodes(core):
                            if rune != core and \
                               math.hypot(mx - rune.ui_x, my - rune.ui_y) <= rune.ui_radius:
                                dragged_rune = rune; rune.is_dragging = True; break

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                mouse_held    = False
                just_released = True
                if game_state == "RUNE_MENU" and dragged_rune:
                    mx, my = mouse_pos
                    dragged_rune.is_dragging = False
                    core = player.spell_manager.core_tree
                    if my > HEIGHT - 150:
                        core.remove_rune(dragged_rune)
                        if dragged_rune not in inventory: inventory.append(dragged_rune)
                    else:
                        target_slot_id = -1
                        for slot in core.slots:
                            if math.hypot(mx - slot['ui_x'], my - slot['ui_y']) <= 30:
                                target_slot_id = slot['id']; break
                        
                        if target_slot_id != -1:
                            # Try to attach to specific slot
                            core.remove_rune(dragged_rune) # Clear old slot if any
                            ok = core.try_attach_to_slot(dragged_rune, target_slot_id)
                            if ok:
                                if dragged_rune in inventory: inventory.remove(dragged_rune)
                            else:
                                if dragged_rune not in inventory: inventory.append(dragged_rune)
                        else:
                            # Not dropped on a slot, return to inventory
                            core.remove_rune(dragged_rune)
                            if dragged_rune not in inventory: inventory.append(dragged_rune)
                    dragged_rune = None

        # ── WEAPON SELECT ──────────────────────────────────────
        if game_state == "WEAPON_SELECT":
            hovered_card = draw_weapon_select(screen, font, font_l, mouse_pos, t_anim)
            pygame.display.flip()
            continue

        # ── LEVEL UP SELECT ────────────────────────────────────
        if game_state == "LEVEL_UP_SELECT":
            hovered_lvl_up = draw_level_up_select(screen, font, font_l, level_up_options)
            pygame.display.flip()
            continue

        # ── PLAYING ────────────────────────────────────────────
        if game_state == "PLAYING":
            if not player.alive:
                game_state = "GAME_OVER"

            cx = player.x - WIDTH // 2
            cy = player.y - HEIGHT // 2
            world_mx = mouse_pos[0] + cx
            world_my = mouse_pos[1] + cy

            player_ihit = max(0.0, player_ihit - dt)

            # Level up → select
            if player.pending_level_ups > 0:
                player.pending_level_ups -= 1
                level_up_options = [get_random_rune() for _ in range(3)]
                game_state = "LEVEL_UP_SELECT"

            # Spawn
            spawn_timer += dt
            if spawn_timer >= SPAWN_INT:
                spawn_timer = 0.0
                wave_num   += 1
                
                hp_mult = 1.0 + (wave_num * 0.05)
                speed_mult = 1.0 + (wave_num * 0.02)

                if wave_num == BOSS_WAVE:
                    wave_notif_text = "WARNING: BOSS INCOMING!"
                elif wave_num == 10:
                    wave_notif_text = f"WAVE {wave_num} - TANK ENEMIES APPEAR!"
                elif wave_num == 5:
                    wave_notif_text = f"WAVE {wave_num} - FAST ENEMIES APPEAR!"
                else:
                    wave_notif_text = f"WAVE {wave_num}"
                wave_notif_timer = 3.0
                
                sx, sy = random_spawn_pos(player.x, player.y)
                if wave_num >= BOSS_WAVE and boss is None:
                    boss = Boss(sx, sy, hp_mult=hp_mult, speed_mult=speed_mult)
                else:
                    # Tăng nhẹ số lượng quái max để màn chơi đông hơn
                    count = min(1 + wave_num // 3, 10)
                    for _ in range(count):
                        ex, ey = random_spawn_pos(player.x, player.y,
                                                  500 + random.randint(-100, 100))
                        rand_val = random.random()
                        if wave_num >= 10 and rand_val < 0.15:
                            enemies.append(TankEnemy(ex, ey, hp_mult=hp_mult, speed_mult=speed_mult))
                        elif wave_num >= 5 and rand_val < 0.35:
                            enemies.append(FastEnemy(ex, ey, hp_mult=hp_mult, speed_mult=speed_mult))
                        elif wave_num >= 3 and rand_val < 0.65:
                            enemies.append(RangedEnemy(ex, ey, hp_mult=hp_mult, speed_mult=speed_mult))
                        else:
                            enemies.append(Enemy(ex, ey, hp_mult=hp_mult, speed_mult=speed_mult))

            # Lightning movement logic
            base_speed = Player.BASE_SPEED
            is_lightning = isinstance(player.weapon, LightningWeapon)
            
            if is_lightning and mouse_held and not player.weapon.is_overloaded:
                player.speed = 0 # Can't move while zapping
            elif is_lightning and player.weapon.is_overloaded:
                player.speed = base_speed * 1.5
            else:
                player.speed = base_speed

            player.update(dt, False, 0, 0)

            # Weapon update
            # Weapon update
           # Weapon update
            if player.weapon:
                all_entities = [e for e in enemies if e.alive] + \
                               ([boss] if boss and boss.alive else [])
                               
                # [THÊM DÒNG NÀY] Cung cấp danh sách quái cho các Rune (như Bounce) sử dụng
                player.spell_manager.enemies_ref = all_entities 
                
                player.weapon.update(dt, mouse_held, just_released,
                                     world_mx, world_my, player, all_entities)

                # Fire / Ice → create weapon projectile
                for shot in player.weapon.pending_shots:
                    # [QUAN TRỌNG] Bắt buộc gọi on_spawn để khởi tạo các chỉ số Rune 
                    # (Làm điều này sẽ sửa luôn lỗi các Rune tăng Damage không hoạt động)
                    if hasattr(shot, 'core_tree') and shot.core_tree:
                        shot.core_tree.on_spawn(shot, player.spell_manager)
                        
                    weapon_projectiles.append(shot)

                # [THÊM MỚI] Chuyển đạn do Rune tạo ra (SplitRune) vào luồng xử lý chính của Game
                if player.spell_manager.projectiles:
                    for shot in player.spell_manager.projectiles:
                        weapon_projectiles.append(shot)
                    player.spell_manager.projectiles.clear()

                # [THÊM MỚI] Chuyển đạn do Rune tạo ra (SplitRune) vào luồng xử lý chính của Game
                if player.spell_manager.projectiles:
                    for shot in player.spell_manager.projectiles:
                        weapon_projectiles.append(shot)
                    player.spell_manager.projectiles.clear() # Dọn dẹp sau khi đã chuyển

                # Lightning → direct damage
                if hasattr(player.weapon, 'pending_damage'):
                    for (target, dmg) in player.weapon.pending_damage:
                        if target.alive:
                            target.take_damage(dmg)

                # Lightning overload spark + spark damage
                if isinstance(player.weapon, LightningWeapon) and player.weapon.is_overloaded:
                    keys = pygame.key.get_pressed()
                    if any(keys[k] for k in [pygame.K_w, pygame.K_s, pygame.K_a, pygame.K_d]):
                        player.weapon.emit_move_spark(player.x, player.y)
                        for e in all_entities:
                            if e.alive and math.hypot(e.x-player.x, e.y-player.y) < 90:
                                e.take_damage(8 * dt)

            # Update weapon projectiles + collision
            for wp in weapon_projectiles[:]:
                wp.update(dt)
                hit = False
                targets = [e for e in enemies if e.alive] + ([boss] if boss and boss.alive else [])
                for t in targets:
                    if wp.check_collision(t):
                        # Pierce logic
                        if wp.pierce:
                            if t in wp.hit_enemies:
                                continue
                            wp.hit_enemies.add(t)
                        else:
                            hit = True
                        
                        t.take_damage(wp.damage)
                        for eff in wp.status_effects:
                            t.add_status(eff)
                        
                        # Hook on_hit
                        if hasattr(wp, 'core_tree') and wp.core_tree:
                            wp.core_tree.on_hit(wp, t, getattr(wp, 'spell_manager', player.spell_manager))
                        
                        # [SỬA LỖI] Kiểm tra xem đạn có đang kích hoạt Nảy không
                        is_bouncing = getattr(wp, 'is_bouncing', False)
                        
                        if not getattr(wp, 'pierce', False) and not is_bouncing:
                            wp.alive = False  # Xóa đạn bình thường nếu không xuyên và không nảy
                            hit = True
                            break
                            
                        if is_bouncing:
                            wp.is_bouncing = False # Reset cờ nảy để lần chạm tiếp theo còn xét tiếp
                            hit = True
                            break # Break để tránh 1 frame đạn va chạm nhiều quái
                        
                        if not wp.pierce:
                            wp.alive = False
                            hit = True
                            break
                if not wp.alive:
                    weapon_projectiles.remove(wp)

            # Boss
            if boss:
                if boss.alive:
                    boss.update(dt, player.x, player.y)
                    aoe = boss.check_aoe_hit(player.x, player.y)
                    if aoe > 0 and player_ihit <= 0:
                        player.take_damage(aoe * dt)
                    chg = boss.check_charge_hit(player.x, player.y, player.radius)
                    if chg > 0 and player_ihit <= 0:
                        player.take_damage(chg); player_ihit = HIT_CD
                    if math.hypot(player.x-boss.x, player.y-boss.y) < player.radius+boss.radius \
                       and player_ihit <= 0:
                        player.take_damage(20); player_ihit = HIT_CD
                    if boss.pending_summon:
                        boss.pending_summon = False
                        for _ in range(Boss.SUMMON_COUNT):
                            ex, ey = random_spawn_pos(boss.x, boss.y, 200)
                            enemies.append(Enemy(ex, ey))
                    # Bullet-boss collision (weapon projectiles)
                    # Already handled above in targets loop
                else:
                    gems.append(ExpGem(boss.x, boss.y, boss.xp_value)); boss = None

            # Enemies
            for enemy in enemies[:]:
                if not enemy.alive: continue
                enemy.update(dt, player.x, player.y)
                if math.hypot(player.x-enemy.x, player.y-enemy.y) < player.radius+enemy.radius \
                   and player_ihit <= 0:
                    dmg = getattr(enemy, 'damage', 10.0)
                    player.take_damage(dmg); player_ihit = HIT_CD
                if isinstance(enemy, RangedEnemy) and enemy.can_fire():
                    enemy.reset_fire_timer()
                    enemy_bullets.append(EnemyBullet(enemy.x, enemy.y, player.x, player.y))

            for enemy in enemies[:]:
                if not enemy.alive:
                    gems.append(ExpGem(enemy.x, enemy.y, enemy.xp_value))
                    enemies.remove(enemy)

            # Enemy bullets
            for eb in enemy_bullets[:]:
                eb.update(dt)
                if math.hypot(player.x-eb.x, player.y-eb.y) < player.radius+eb.radius:
                    if player_ihit <= 0:
                        player.take_damage(eb.damage); player_ihit = HIT_CD
                    eb.alive = False
                if not eb.alive: enemy_bullets.remove(eb)

            # Gems
            for gem in gems[:]:
                if math.hypot(player.x-gem.x, player.y-gem.y) < player.radius+gem.radius:
                    player.gain_exp(gem.amount); gems.remove(gem)

        # ── DRAW ───────────────────────────────────────────────
        screen.fill(BLACK)

        if game_state in ("PLAYING", "GAME_OVER"):
            cx = player.x - WIDTH // 2
            cy = player.y - HEIGHT // 2
            draw_grid(screen, cx, cy)

            for gem in gems: gem.draw(screen, cx, cy)
            for eb  in enemy_bullets: eb.draw(screen, cx, cy)

            # Weapon projectiles
            for wp in weapon_projectiles: wp.draw(screen, cx, cy)

            for en in enemies:
                if en.alive: en.draw(screen, cx, cy)
            if boss and boss.alive: boss.draw(screen, cx, cy)

            # Weapon effects (lightning arcs, ice preview)
            if player.weapon:
                player.weapon.draw_preview(screen, cx, cy, player)
                player.weapon.draw_effects(screen, cx, cy)

            player.draw(screen, cx, cy)
            player.spell_manager.draw(screen, cx, cy)

            draw_hud(screen, player, boss, wave_num, font, font_l)

            if wave_notif_timer > 0:
                wave_notif_timer -= dt
                alpha = min(255, max(0, int((wave_notif_timer / 3.0) * 255 * 2)))
                notif_surf = font_l.render(wave_notif_text, True, YELLOW)
                notif_surf.set_alpha(alpha)
                screen.blit(notif_surf, (WIDTH//2 - notif_surf.get_width()//2, HEIGHT//4))

            if game_state == "GAME_OVER":
                ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                ov.fill((0, 0, 0, 160)); screen.blit(ov, (0, 0))
                go = font_l.render("GAME OVER", True, RED)
                screen.blit(go, (WIDTH//2 - go.get_width()//2, HEIGHT//2 - 40))
                r  = font.render("Press R to restart", True, WHITE)
                screen.blit(r,  (WIDTH//2 - r.get_width()//2,  HEIGHT//2 + 10))

        elif game_state == "RUNE_MENU":
            core = player.spell_manager.core_tree
            update_tree_layout(core, WIDTH // 2, 80)
            if dragged_rune:
                dragged_rune.ui_x, dragged_rune.ui_y = mouse_pos

            used = core.get_total_cost()
            screen.blit(font_l.render(f"CAPACITY: {core.max_capacity - used}/{core.max_capacity}",
                                      True, YELLOW), (20, 20))
            draw_stats_panel(screen, font, font_l, player.weapon_type)
            draw_connections(screen, core)
            draw_slots(screen, core, font)
            for nd in get_all_nodes(core):
                if nd != dragged_rune: nd.draw_node(screen, font)

            pygame.draw.rect(screen, (40, 40, 40), (0, HEIGHT - 150, WIDTH, 150))
            screen.blit(font_l.render("INVENTORY (Drag to equip)", True, WHITE), (10, HEIGHT - 140))
            for i, rune in enumerate(inventory):
                if not rune.is_dragging:
                    rune.ui_x = 50 + i * 80
                    rune.ui_y = HEIGHT - 70
                rune.draw_node(screen, font)
                screen.blit(font.render(f"Cost:{rune.cost}", True, GREEN),
                            (rune.ui_x - 20, rune.ui_y + 30))
            if dragged_rune:
                dragged_rune.draw_node(screen, font)
                tt = font.render(dragged_rune.name, True, WHITE, BLACK)
                screen.blit(tt, (mouse_pos[0] + 20, mouse_pos[1] - 20))

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()