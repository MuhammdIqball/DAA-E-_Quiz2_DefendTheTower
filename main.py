"""
main.py  (Puzzle Mode — Ticket 4)
==================================
Pivot ke game puzzle logika graf (bottleneck puzzle).

Alur baru:
  MENU → Start → _load_level → PREP (puzzle)
  PREP:  player pasang blok (klik kiri) / hapus (klik kanan)
         ENTER / blok habis → _evaluate_puzzle() via Dijkstra
         → STATE_WIN (level clear) / STATE_LOSE (jalur masih ada)
  WIN  : level < MAX → LEVEL_TRANS → level berikutnya
         level = MAX → overlay "ALL CLEAR"
  LOSE : overlay + highlight jalur yang ditemukan Dijkstra (feedback visual)

Pembagian modul:
  main.py        → loop, event, state, render
  pathfinding.py → BFS (real-time) + Dijkstra (evaluasi puzzle)
  entities.py    → Tower (visual blok pemain)
  src/levels.py  → puzzle level configs (block_count, pre_obstacles)
  src/ui.py      → Button, MainMenu, InstructionsScreen, LevelTransition
"""

import pygame
import sys
import time

from pathfinding import find_shortest_path, dijkstra
from entities import Tower
from src.levels import LEVEL_CONFIGS, MAX_LEVEL, build_grid

# =============================================================================
#  KONSTANTA
# =============================================================================
SCREEN_W  = 800
SCREEN_H  = 600
CELL_SIZE = 40
COLS      = SCREEN_W // CELL_SIZE   # 20
ROWS      = SCREEN_H // CELL_SIZE   # 15

FPS = 60

# -- Game States --------------------------------------------------------------
STATE_PREP  = "prep"
STATE_WIN   = "win"
STATE_LOSE  = "lose"

# -- Palet Warna --------------------------------------------------------------
C_BG        = ( 28,  34,  42)
C_CELL      = ( 40,  50,  60)
C_GRID_LINE = ( 55,  65,  75)
C_PATH      = ( 60, 110, 170)
C_SPAWN     = (  0, 190,  90)
C_BASE      = (255, 160,   0)
C_NO_BUILD  = ( 38,  55,  35)
C_WALL      = ( 65,  75,  90)   # obstacle permanen (lebih terang dari C_CELL)
C_FAIL_PATH = (190,  60,  40)   # jalur Dijkstra saat LOSE (merah-oranye)
C_HUD_TEXT  = (210, 210, 210)
C_HUD_WARN  = (255, 100, 100)
C_HUD_HINT  = (180, 220, 160)
C_WIN       = ( 50, 200, 100)
C_LOSE      = (200,  50,  50)
C_INV_FULL  = ( 70, 140, 220)   # blok inventory tersedia
C_INV_EMPTY = ( 45,  55,  65)   # blok inventory sudah dipakai


# =============================================================================
#  CLASS GAME
# =============================================================================
class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("Algorithmic Tower Defense  |  Dijkstra Puzzle")
        self.clock = pygame.time.Clock()

        self.font      = pygame.font.SysFont("consolas", 13)
        self.font_bold = pygame.font.SysFont("consolas", 15, bold=True)

        # -- Game state -------------------------------------------------------
        self.state         = STATE_PREP
        self.current_level = 1

        # -- Level objects (diisi saat _load_level) ---------------------------
        self.grid              = None
        self.towers            = []      # hanya player-placed towers
        self.spawn_pos         = None
        self.base_pos          = None
        self.no_build_set      = set()
        self.pre_obstacles_set = set()   # posisi obstacle permanen (tidak bisa dihapus)
        self.current_path      = None
        self.failure_path      = None    # jalur Dijkstra saat LOSE (untuk visualisasi)

        # -- Inventory --------------------------------------------------------
        self.blocks_remaining = 0
        self.block_count_max  = 0

        # -- Drag-to-build state ----------------------------------------------
        self.dragging      = False
        self.dragged_cells = set()

        # Mulai langsung di Level 1
        self._load_level(1)

    # =========================================================================
    #  LOAD LEVEL
    # =========================================================================
    def _load_level(self, level_num):
        """Inisialisasi semua state untuk level puzzle yang diberikan."""
        cfg = LEVEL_CONFIGS[level_num]
        self.current_level     = level_num
        self.spawn_pos         = cfg["spawn"]
        self.base_pos          = cfg["base"]
        self.no_build_set      = cfg.get("no_build_zones", set())
        self.pre_obstacles_set = set(map(tuple, cfg["pre_obstacles"]))

        self.grid          = build_grid(level_num)
        self.towers        = []
        self.failure_path  = None
        self.dijkstra_time_ms = None   # waktu eksekusi Dijkstra terakhir (ms)
        self.current_path  = find_shortest_path(
            self.grid, self.spawn_pos, self.base_pos, ROWS, COLS)

        self.block_count_max  = cfg["block_count"]
        self.blocks_remaining = cfg["block_count"]

        self.dragging      = False
        self.dragged_cells = set()
        self.state         = STATE_PREP

    # =========================================================================
    #  EVENT HANDLING
    # =========================================================================
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # ---- LEVEL TRANSITION -------------------------------------------
            # (removed — level-clear auto-advances in _evaluate_puzzle)

            # ---- GAMEPLAY ---------------------------------------------------
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    self._load_level(self.current_level)
                elif event.key == pygame.K_ESCAPE:
                    self._load_level(1)   # ESC = kembali ke Level 1
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    if self.state == STATE_PREP:
                        self._evaluate_puzzle()

            if self.state == STATE_PREP:
                # -- Klik kiri: drag-to-build ----------------------------
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

                # -- Klik kanan: hapus blok yang dipasang pemain ----------
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                    mx, my = event.pos
                    self.try_remove_tower(mx // CELL_SIZE, my // CELL_SIZE)

    # =========================================================================
    #  PENEMPATAN BLOK (klik kiri)
    # =========================================================================
    def try_place_tower(self, gx, gy):
        """
        Pasang blok di (gx, gy). Inventaris berkurang 1.
        Auto-evaluate saat inventaris mencapai 0.

        Validasi:
        1. Batas grid.
        2. Bukan Spawn / Base.
        3. Sel harus 0 (bukan obstacle=1 atau no-build=2).
        4. Masih punya blok (blocks_remaining > 0).
        5. Anti-duplikat dalam 1 gesture drag.
        """
        if not (0 <= gx < COLS and 0 <= gy < ROWS):
            return
        if (gx, gy) == self.spawn_pos or (gx, gy) == self.base_pos:
            return
        if self.grid[gy][gx] != 0:
            return
        if self.blocks_remaining <= 0:
            return
        if (gx, gy) in self.dragged_cells:
            return

        self.dragged_cells.add((gx, gy))
        self.grid[gy][gx] = 1
        self.towers.append(Tower(gx, gy, CELL_SIZE))
        self.blocks_remaining -= 1

        # Update BFS path (preview jalur musuh real-time)
        self.current_path = find_shortest_path(
            self.grid, self.spawn_pos, self.base_pos, ROWS, COLS)

        # Auto-evaluate saat inventaris habis
        if self.blocks_remaining == 0:
            self._evaluate_puzzle()

    # =========================================================================
    #  HAPUS BLOK (klik kanan)
    # =========================================================================
    def try_remove_tower(self, gx, gy):
        """
        Hapus blok yang dipasang PEMAIN di (gx, gy).
        Obstacle permanen tidak bisa dihapus.
        Inventaris bertambah 1.
        """
        if not (0 <= gx < COLS and 0 <= gy < ROWS):
            return
        # Hanya bisa hapus jika itu player-placed tower (bukan pre-obstacle)
        if self.grid[gy][gx] != 1:
            return
        if (gx, gy) in self.pre_obstacles_set:
            return

        self.grid[gy][gx] = 0
        self.towers = [t for t in self.towers
                       if not (t.grid_x == gx and t.grid_y == gy)]
        self.blocks_remaining += 1

        # Update BFS path
        self.current_path = find_shortest_path(
            self.grid, self.spawn_pos, self.base_pos, ROWS, COLS)

    # =========================================================================
    #  EVALUASI PUZZLE (Dijkstra)
    # =========================================================================
    def _evaluate_puzzle(self):
        """
        Jalankan Dijkstra dari SPAWN ke BASE untuk menentukan WIN/LOSE.

        - Dijkstra mengembalikan None  →  BASE tidak dapat dijangkau → WIN.
        - Dijkstra menemukan jalur     →  BASE masih bisa dijangkau  → LOSE.
          Jalur yang ditemukan disimpan ke self.failure_path untuk divisualisasi
          agar pemain tahu di mana "kebocoran" pertahanan mereka.
        """
        # Hentikan drag sebelum evaluasi
        self.dragging      = False
        self.dragged_cells = set()

        t0     = time.perf_counter()
        result = dijkstra(self.grid, self.spawn_pos, self.base_pos, ROWS, COLS)
        self.dijkstra_time_ms = (time.perf_counter() - t0) * 1000

        if result is None:
            # Dijkstra: Base tidak reachable → level clear!
            if self.current_level < MAX_LEVEL:
                self._load_level(self.current_level + 1)  # langsung lanjut
            else:
                self.state = STATE_WIN
        else:
            # Dijkstra: jalur masih ditemukan → pemain kalah
            self.failure_path = result   # disimpan untuk visualisasi
            self.current_path = result
            self.state        = STATE_LOSE

    # =========================================================================
    #  UPDATE (minimal — puzzle mode tidak punya enemies/timer)
    # =========================================================================
    def update(self):
        # Puzzle mode: tidak ada update logic aktif; semua event-driven
        pass

    # =========================================================================
    #  RENDERING
    # =========================================================================
    def draw_grid(self):
        """
        Warna sel:
          failure_path (saat LOSE) : C_FAIL_PATH  merah-oranye (jalur Dijkstra)
          SPAWN                    : C_SPAWN       hijau
          BASE                     : C_BASE        oranye
          grid == 2 (no-build)     : C_NO_BUILD    hijau tua
          grid == 1 (obstacle)     : C_WALL        abu lebih terang
          in current_path          : C_PATH        biru (preview BFS)
          grid == 0 kosong         : C_CELL        abu gelap
        """
        path_set    = set(self.current_path)  if self.current_path  else set()
        failure_set = set(self.failure_path)  if self.failure_path  else set()

        for row in range(ROWS):
            for col in range(COLS):
                rect = pygame.Rect(col * CELL_SIZE, row * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                pos  = (col, row)

                if pos in failure_set and self.state == STATE_LOSE:
                    pygame.draw.rect(self.screen, C_FAIL_PATH, rect)
                elif pos == self.spawn_pos:
                    pygame.draw.rect(self.screen, C_SPAWN, rect)
                elif pos == self.base_pos:
                    pygame.draw.rect(self.screen, C_BASE, rect)
                elif self.grid[row][col] == 2:
                    pygame.draw.rect(self.screen, C_NO_BUILD, rect)
                elif self.grid[row][col] == 1:
                    # Obstacle: warna berbeda untuk permanent vs player-placed
                    if pos in self.pre_obstacles_set:
                        pygame.draw.rect(self.screen, C_WALL, rect)
                    else:
                        pygame.draw.rect(self.screen, C_CELL, rect)
                elif pos in path_set and self.state == STATE_PREP:
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
        """HUD info puzzle di kiri atas."""
        cfg        = LEVEL_CONFIGS[self.current_level]
        level_name = cfg["name"]
        hint       = cfg["hint"]

        if self.state == STATE_PREP:
            lines = [
                (level_name,                             C_HUD_TEXT,  True),
                (f"Blok tersisa : {self.blocks_remaining} / {self.block_count_max}",
                                                         C_HUD_TEXT,  False),
            ]
        elif self.state == STATE_LOSE:
            lines = [
                (level_name,                             C_HUD_TEXT,  True),
                ("Dijkstra masih menemukan jalan!",      C_HUD_WARN,  False),
            ]
        else:
            lines = [
                (level_name,                             C_HUD_TEXT,  True),
            ]

        pad = 8
        bg  = pygame.Surface((310, len(lines) * 17 + pad * 2), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 150))
        self.screen.blit(bg, (0, 0))

        for i, (text, color, bold) in enumerate(lines):
            font = self.font_bold if bold else self.font
            lbl  = font.render(text, True, color)
            self.screen.blit(lbl, (pad, pad + i * 17))

    def draw_inventory(self):
        """
        Bar inventaris blok di pojok kanan atas.
        Kotak penuh = blok tersedia, kotak kosong = blok sudah dipakai.
        """
        if self.state not in (STATE_PREP, STATE_LOSE):
            return

        box_size = 28
        gap      = 6
        total_w  = self.block_count_max * (box_size + gap) - gap
        start_x  = SCREEN_W - total_w - 12
        start_y  = 12

        # Label
        lbl = self.font_bold.render("BLOK:", True, C_HUD_TEXT)
        self.screen.blit(lbl, (start_x - lbl.get_width() - 8, start_y + 6))

        for i in range(self.block_count_max):
            x    = start_x + i * (box_size + gap)
            rect = pygame.Rect(x, start_y, box_size, box_size)
            # Blok ke-i tersedia jika i < blocks_remaining
            color = C_INV_FULL if i < self.blocks_remaining else C_INV_EMPTY
            pygame.draw.rect(self.screen, color, rect, border_radius=4)
            pygame.draw.rect(self.screen, (100, 130, 160), rect, 2, border_radius=4)

    def draw_overlay(self):
        """WIN / LOSE full-screen overlay."""
        if self.state not in (STATE_WIN, STATE_LOSE):
            return

        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 155))
        self.screen.blit(overlay, (0, 0))

        font_big   = pygame.font.SysFont("consolas", 64, bold=True)
        font_small = pygame.font.SysFont("consolas", 20)

        if self.state == STATE_WIN:
            title_text  = "ALL LEVELS CLEAR!"
            title_color = C_WIN
            sub_text    = "Dijkstra: Semua jalur berhasil diblokir!"
            sub_color   = (180, 255, 180)
        else:
            title_text  = "YOU LOSE"
            title_color = C_LOSE
            sub_text    = "Dijkstra masih menemukan jalur ke Base."
            sub_color   = (255, 180, 180)

        title = font_big.render(title_text,  True, title_color)
        sub   = font_small.render(sub_text,  True, sub_color)
        hint1 = font_small.render("Jalur merah = rute yang ditemukan Dijkstra.", True, (200, 150, 130))
        hint2 = font_small.render("R / ESC = Main ulang dari Level 1", True, C_HUD_TEXT)

        # Waktu eksekusi Dijkstra
        if self.dijkstra_time_ms is not None:
            t_str  = f"Dijkstra: {self.dijkstra_time_ms:.4f} ms"
            t_surf = font_small.render(t_str, True, (160, 200, 255))
        else:
            t_surf = None

        cx = SCREEN_W // 2
        cy = SCREEN_H // 2

        self.screen.blit(title, (cx - title.get_width() // 2, cy - 105))
        self.screen.blit(sub,   (cx - sub.get_width()   // 2, cy -  10))
        if self.state == STATE_LOSE:
            self.screen.blit(hint1, (cx - hint1.get_width() // 2, cy + 22))
        self.screen.blit(hint2, (cx - hint2.get_width() // 2, cy + 52))
        if t_surf:
            self.screen.blit(t_surf, (cx - t_surf.get_width() // 2, cy + 82))

    # =========================================================================
    #  GAME LOOP UTAMA
    # =========================================================================
    def run(self):
        while True:
            self.handle_events()
            self.update()

            self.screen.fill(C_BG)
            if self.grid:
                self.draw_grid()
                for tower in self.towers:
                    tower.draw(self.screen)
                self.draw_hud()
                self.draw_inventory()
                self.draw_overlay()

            pygame.display.flip()
            self.clock.tick(FPS)


# =============================================================================
#  ENTRY POINT
# =============================================================================
if __name__ == "__main__":
    game = Game()
    game.run()
