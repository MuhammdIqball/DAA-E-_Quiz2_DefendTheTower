"""
main.py
=======
Entry point game Tower Defense berbasis algoritma BFS.

Tanggung jawab modul ini:
- Inisialisasi Pygame & window
- Game loop utama (handle event -> update -> render)
- State Manager: MENU -> INSTRUCTIONS -> PREP -> BATTLE -> WIN/LOSE/LEVEL_TRANS
- Level transition (Level 1 -> Level 2)
- Drag-to-build (MOUSEBUTTONDOWN / MOUSEMOTION / MOUSEBUTTONUP)

Pembagian modul:
  main.py         -> inisialisasi, loop, event, render, state
  pathfinding.py  -> logika graf, BFS, reachability
  entities.py     -> Tower, Enemy, Timer
  src/levels.py   -> konfigurasi level (no-build zones, pre-obstacles)
  src/ui.py       -> Button, MainMenu, InstructionsScreen, LevelTransition
"""

import pygame
import sys

from pathfinding import find_shortest_path, is_path_exists
from entities import Tower, Enemy, Timer
from src.levels import LEVEL_CONFIGS, MAX_LEVEL, build_grid
from src.ui import MainMenu, InstructionsScreen, LevelTransition

# =============================================================================
#  KONSTANTA
# =============================================================================
SCREEN_W  = 800
SCREEN_H  = 600
CELL_SIZE = 40
COLS      = SCREEN_W // CELL_SIZE   # 20
ROWS      = SCREEN_H // CELL_SIZE   # 15

FPS                  = 60
ENEMY_SPAWN_INTERVAL = 120   # frame antar spawn musuh saat Battle Phase

# -- Game States --------------------------------------------------------------
STATE_MENU         = "menu"
STATE_INSTRUCTIONS = "instructions"
STATE_PREP         = "prep"
STATE_BATTLE       = "battle"
STATE_WIN          = "win"          # final win (level terakhir clear)
STATE_LOSE         = "lose"
STATE_LEVEL_TRANS  = "level_trans"  # level N clear -> transisi ke level N+1

# -- Palet Warna --------------------------------------------------------------
C_BG        = ( 28,  34,  42)
C_CELL      = ( 40,  50,  60)
C_GRID_LINE = ( 55,  65,  75)
C_PATH      = ( 60, 110, 170)
C_SPAWN     = (  0, 190,  90)
C_BASE      = (255, 160,   0)
C_NO_BUILD  = ( 38,  55,  35)   # rawa / no-build zone (hijau tua gelap)
C_HUD_TEXT  = (210, 210, 210)
C_HUD_WARN  = (255, 100, 100)
C_WIN       = ( 50, 200, 100)
C_LOSE      = (200,  50,  50)


# =============================================================================
#  CLASS GAME
# =============================================================================
class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("Algorithmic Tower Defense  |  BFS Pathfinding")
        self.clock = pygame.time.Clock()

        self.font      = pygame.font.SysFont("consolas", 13)
        self.font_bold = pygame.font.SysFont("consolas", 15, bold=True)

        # -- UI screens -------------------------------------------------------
        self.main_menu    = MainMenu(self.screen)
        self.instr_screen = InstructionsScreen(self.screen)
        self.level_trans  = None   # dibuat saat dibutuhkan

        # -- Game state -------------------------------------------------------
        self.state         = STATE_MENU
        self.current_level = 1

        # -- Level objects (diisi saat _load_level) ---------------------------
        self.grid         = None
        self.towers       = []
        self.enemies      = []
        self.timer        = None
        self.spawn_pos    = None
        self.base_pos     = None
        self.no_build_set = set()
        self.current_path = None

        # -- Battle counters --------------------------------------------------
        self.spawn_timer  = 0
        self.enemies_lost = 0

        # -- Drag-to-build state ----------------------------------------------
        self.dragging      = False
        self.dragged_cells = set()   # sel yang sudah dipasang dalam 1 gesture drag

    # =========================================================================
    #  LOAD LEVEL
    # =========================================================================
    def _load_level(self, level_num):
        """Inisialisasi semua state untuk level yang diberikan."""
        cfg = LEVEL_CONFIGS[level_num]
        self.current_level = level_num
        self.spawn_pos     = cfg["spawn"]
        self.base_pos      = cfg["base"]
        self.no_build_set  = cfg["no_build_zones"]

        self.grid      = build_grid(level_num)
        self.towers    = []
        self.enemies   = []
        self.timer     = Timer(cfg["prep_duration"], FPS)
        self.spawn_timer   = 0
        self.enemies_lost  = 0
        self.dragging      = False
        self.dragged_cells = set()
        self.state         = STATE_PREP

        # Buat Tower visual untuk pre-placed obstacles
        for (col, row) in cfg["pre_obstacles"]:
            if 0 <= row < ROWS and 0 <= col < COLS:
                self.towers.append(Tower(col, row, CELL_SIZE))

        self.current_path = find_shortest_path(
            self.grid, self.spawn_pos, self.base_pos, ROWS, COLS)

    # =========================================================================
    #  EVENT HANDLING
    # =========================================================================
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # ---- MENU -------------------------------------------------------
            if self.state == STATE_MENU:
                action = self.main_menu.handle_event(event)
                if action == "start":
                    self._load_level(1)
                elif action == "instructions":
                    self.state = STATE_INSTRUCTIONS
                elif action == "exit":
                    pygame.quit()
                    sys.exit()

            # ---- INSTRUCTIONS -----------------------------------------------
            elif self.state == STATE_INSTRUCTIONS:
                if self.instr_screen.handle_event(event):
                    self.state = STATE_MENU

            # ---- LEVEL TRANSITION -------------------------------------------
            elif self.state == STATE_LEVEL_TRANS:
                if self.level_trans and self.level_trans.handle_event(event):
                    self._load_level(self.current_level + 1)

            # ---- GAMEPLAY ---------------------------------------------------
            else:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        self._load_level(self.current_level)
                    if event.key == pygame.K_ESCAPE:
                        self.state = STATE_MENU

                # Drag-to-build (hanya saat PREP)
                if self.state == STATE_PREP:
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        self.dragging      = True
                        self.dragged_cells = set()
                        mx, my = event.pos
                        self.try_place_tower(mx // CELL_SIZE, my // CELL_SIZE)

                    elif event.type == pygame.MOUSEMOTION and self.dragging:
                        mx, my = event.pos
                        self.try_place_tower(mx // CELL_SIZE, my // CELL_SIZE)

                    elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                        self.dragging      = False
                        self.dragged_cells = set()

    # =========================================================================
    #  PENEMPATAN TOWER
    # =========================================================================
    def try_place_tower(self, gx, gy):
        """
        Pasang tower di sel (gx, gy).

        Validasi:
        1. Batas grid.
        2. Bukan Spawn / Base.
        3. Sel harus == 0 (bukan tower=1 dan bukan no-build zone=2).
        4. Belum dipasang dalam gesture drag saat ini (anti-duplikat).
        """
        if not (0 <= gx < COLS and 0 <= gy < ROWS):
            return
        if (gx, gy) == self.spawn_pos or (gx, gy) == self.base_pos:
            return
        if self.grid[gy][gx] != 0:   # 1=tower, 2=no-build zone
            return
        if (gx, gy) in self.dragged_cells:
            return

        self.dragged_cells.add((gx, gy))
        self.grid[gy][gx] = 1
        self.towers.append(Tower(gx, gy, CELL_SIZE))

        # Perbarui jalur BFS (bisa None jika semua jalur terblokir)
        self.current_path = find_shortest_path(
            self.grid, self.spawn_pos, self.base_pos, ROWS, COLS)

        # Dynamic rerouting semua musuh aktif
        for enemy in self.enemies:
            enemy.set_path(self.current_path)

    # =========================================================================
    #  SPAWN MUSUH
    # =========================================================================
    def spawn_enemy(self):
        path = find_shortest_path(self.grid, self.spawn_pos, self.base_pos, ROWS, COLS)
        if path:
            self.enemies.append(Enemy(self.spawn_pos, CELL_SIZE, path))

    # =========================================================================
    #  UPDATE (LOGIC)
    # =========================================================================
    def update(self):
        if self.state in (STATE_MENU, STATE_INSTRUCTIONS,
                          STATE_LEVEL_TRANS, STATE_WIN, STATE_LOSE):
            return

        # -- PREPARATION PHASE ------------------------------------------------
        if self.state == STATE_PREP:
            self.timer.update()
            if self.timer.finished:
                self._evaluate_reachability()
            return

        # -- BATTLE PHASE -----------------------------------------------------
        if self.state == STATE_BATTLE:
            self.spawn_timer += 1
            if self.spawn_timer >= ENEMY_SPAWN_INTERVAL:
                self.spawn_timer = 0
                self.spawn_enemy()

            for enemy in self.enemies:
                enemy.update()

            reached = [e for e in self.enemies if e.reached_base]
            if reached:
                self.enemies_lost += len(reached)
                self.state = STATE_LOSE
                return

            self.enemies = [e for e in self.enemies if not e.reached_base and e.alive]

    # =========================================================================
    #  REACHABILITY CHECK (akhir Preparation Phase)
    # =========================================================================
    def _evaluate_reachability(self):
        """
        BFS Reachability Check saat timer PREP habis.

        Logika:
        - BFS dari SPAWN ke BASE.
        - BASE tidak pernah di-visited (no path) -> level clear:
            * Bukan level terakhir -> STATE_LEVEL_TRANS
            * Level terakhir       -> STATE_WIN
        - Path masih ada -> STATE_BATTLE.
        """
        path_exists = is_path_exists(self.grid, self.spawn_pos, self.base_pos, ROWS, COLS)

        if not path_exists:
            if self.current_level < MAX_LEVEL:
                self.level_trans = LevelTransition(
                    self.screen, self.current_level, self.current_level + 1)
                self.state = STATE_LEVEL_TRANS
            else:
                self.state = STATE_WIN
        else:
            self.current_path = find_shortest_path(
                self.grid, self.spawn_pos, self.base_pos, ROWS, COLS)
            self.state = STATE_BATTLE

    # =========================================================================
    #  RENDERING
    # =========================================================================
    def draw_grid(self):
        """
        Warna sel:
          2 (no-build zone) -> C_NO_BUILD (hijau tua gelap / rawa)
          1 (tower)         -> C_CELL (tower visual digambar terpisah di atasnya)
          in path_set       -> C_PATH (biru — jalur BFS aktif)
          0 kosong          -> C_CELL
          SPAWN             -> C_SPAWN (hijau)
          BASE              -> C_BASE  (oranye)
        """
        path_set = set(self.current_path) if self.current_path else set()

        for row in range(ROWS):
            for col in range(COLS):
                rect = pygame.Rect(col * CELL_SIZE, row * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                pos  = (col, row)

                if pos == self.spawn_pos:
                    pygame.draw.rect(self.screen, C_SPAWN, rect)
                elif pos == self.base_pos:
                    pygame.draw.rect(self.screen, C_BASE, rect)
                elif self.grid[row][col] == 2:
                    # No-build zone: rawa — traversable oleh musuh, tidak bisa dibangun
                    pygame.draw.rect(self.screen, C_NO_BUILD, rect)
                elif self.grid[row][col] == 1:
                    pygame.draw.rect(self.screen, C_CELL, rect)
                elif pos in path_set:
                    pygame.draw.rect(self.screen, C_PATH, rect)
                else:
                    pygame.draw.rect(self.screen, C_CELL, rect)

                pygame.draw.rect(self.screen, C_GRID_LINE, rect, 1)

        def label(text, col, row, color=(0, 0, 0)):
            lbl = self.font_bold.render(text, True, color)
            self.screen.blit(lbl, (
                col * CELL_SIZE + CELL_SIZE // 2 - lbl.get_width()  // 2,
                row * CELL_SIZE + CELL_SIZE // 2 - lbl.get_height() // 2,
            ))

        label("S", *self.spawn_pos)
        label("B", *self.base_pos)

    def draw_hud(self):
        """HUD dinamis sesuai state."""
        cfg        = LEVEL_CONFIGS[self.current_level]
        level_name = cfg["name"]

        if self.state == STATE_PREP:
            lines = [
                (f"[{level_name}]  BFS Tower Defense",  C_HUD_TEXT,     True),
                ("[ PREPARATION PHASE ]",                C_WIN,          True),
                (f"Waktu tersisa : {self.timer.seconds_left()}s", C_HUD_TEXT, False),
                (f"Towers        : {len(self.towers)}",  C_HUD_TEXT,     False),
                ("",                                     C_HUD_TEXT,     False),
                ("Drag klik = bangun obstacle",          C_HUD_TEXT,     False),
                ("Blokir SEMUA jalur untuk menang!",     C_WIN,          False),
                ("Hijau tua = No-Build Zone",            (140, 180, 120), False),
                ("R = Restart  |  ESC = Menu",           C_HUD_TEXT,     False),
            ]
        elif self.state == STATE_BATTLE:
            lines = [
                (f"[{level_name}]  BFS Tower Defense",  C_HUD_TEXT,     True),
                ("[ BATTLE PHASE ]",                     C_HUD_WARN,     True),
                (f"Enemies aktif : {len(self.enemies)}", C_HUD_TEXT,     False),
                (f"Reached Base  : {self.enemies_lost}",
                    C_HUD_WARN if self.enemies_lost else C_HUD_TEXT,     False),
                ("",                                     C_HUD_TEXT,     False),
                ("Musuh menuju Base!",                   C_HUD_WARN,     False),
                ("R = Restart  |  ESC = Menu",           C_HUD_TEXT,     False),
            ]
        else:
            lines = [
                (f"[{level_name}]  BFS Tower Defense",  C_HUD_TEXT,     True),
                ("R = Restart  |  ESC = Menu",           C_HUD_TEXT,     False),
            ]

        pad = 8
        bg  = pygame.Surface((295, len(lines) * 17 + pad * 2), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 145))
        self.screen.blit(bg, (0, 0))

        for i, (text, color, bold) in enumerate(lines):
            font = self.font_bold if bold else self.font
            lbl  = font.render(text, True, color)
            self.screen.blit(lbl, (pad, pad + i * 17))

    def draw_timer_bar(self):
        """Progress bar hitungan mundur di bawah layar (hanya saat PREP)."""
        if self.state != STATE_PREP or not self.timer:
            return
        bar_w = int(SCREEN_W * (1.0 - self.timer.progress()))
        bar_h = 8
        bar_y = SCREEN_H - bar_h
        pygame.draw.rect(self.screen, (50, 50, 60), (0, bar_y, SCREEN_W, bar_h))
        ratio = 1.0 - self.timer.progress()
        r_val = int(255 * (1 - ratio))
        g_val = int(255 * ratio)
        pygame.draw.rect(self.screen, (r_val, g_val, 40), (0, bar_y, bar_w, bar_h))

    def draw_overlay(self):
        """WIN / LOSE overlay di atas gameplay."""
        if self.state not in (STATE_WIN, STATE_LOSE):
            return

        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        self.screen.blit(overlay, (0, 0))

        font_big   = pygame.font.SysFont("consolas", 64, bold=True)
        font_small = pygame.font.SysFont("consolas", 22)

        if self.state == STATE_WIN:
            title_text  = "YOU WIN!"
            title_color = C_WIN
            sub_text    = "BFS: Semua jalur berhasil diblokir!"
            sub_color   = (180, 255, 180)
        else:
            title_text  = "YOU LOSE"
            title_color = C_LOSE
            sub_text    = "Musuh berhasil mencapai Base!"
            sub_color   = (255, 180, 180)

        title = font_big.render(title_text, True, title_color)
        sub   = font_small.render(sub_text, True, sub_color)
        hint  = font_small.render("R = Restart  |  ESC = Menu Utama", True, C_HUD_TEXT)

        cx = SCREEN_W // 2
        cy = SCREEN_H // 2
        self.screen.blit(title, (cx - title.get_width()  // 2, cy - 80))
        self.screen.blit(sub,   (cx - sub.get_width()    // 2, cy + 10))
        self.screen.blit(hint,  (cx - hint.get_width()   // 2, cy + 55))

    # =========================================================================
    #  GAME LOOP UTAMA
    # =========================================================================
    def run(self):
        while True:
            self.handle_events()
            self.update()

            if self.state == STATE_MENU:
                self.main_menu.draw()

            elif self.state == STATE_INSTRUCTIONS:
                self.instr_screen.draw()

            elif self.state == STATE_LEVEL_TRANS:
                if self.level_trans:
                    self.level_trans.draw()

            else:
                # Gameplay: PREP / BATTLE / WIN / LOSE
                self.screen.fill(C_BG)
                if self.grid:
                    self.draw_grid()
                    for tower in self.towers:
                        tower.draw(self.screen)
                    for enemy in self.enemies:
                        enemy.draw(self.screen)
                    self.draw_hud()
                    self.draw_timer_bar()
                    self.draw_overlay()

            pygame.display.flip()
            self.clock.tick(FPS)


# =============================================================================
#  ENTRY POINT
# =============================================================================
if __name__ == "__main__":
    game = Game()
    game.run()
