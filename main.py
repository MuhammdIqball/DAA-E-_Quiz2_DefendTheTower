"""
main.py
=======
Entry point game Tower Defense berbasis algoritma BFS.

Tanggung jawab modul ini:
- Inisialisasi Pygame & window
- Game loop utama (handle event → update → render)
- Penanganan klik mouse (penempatan tower + validasi BFS)
- Rendering grafis (grid, path, entities, HUD)
- Game State Manager: PREP → BATTLE → WIN / LOSE

Pembagian modul:
  main.py         → (file ini)  inisialisasi, loop, event, render, state
  pathfinding.py  → logika graf, algoritma BFS, reachability checker
  entities.py     → class Tower, Enemy, Timer
"""

import pygame
import sys

from pathfinding import find_shortest_path, is_path_exists
from entities import Tower, Enemy, Timer

# ─────────────────────────────────────────────
#  KONSTANTA
# ─────────────────────────────────────────────
SCREEN_W   = 800
SCREEN_H   = 600
CELL_SIZE  = 40
COLS       = SCREEN_W // CELL_SIZE   # 20 kolom
ROWS       = SCREEN_H // CELL_SIZE   # 15 baris

SPAWN = (0,  7)   # (col, row) — kiri tengah
BASE  = (19, 7)   # (col, row) — kanan tengah

FPS                  = 60
ENEMY_SPAWN_INTERVAL = 120   # frame antar spawn musuh saat Battle Phase
PREP_DURATION        = 20    # detik durasi Preparation Phase

# ── Game States ──────────────────────────────
STATE_PREP   = "prep"
STATE_BATTLE = "battle"
STATE_WIN    = "win"
STATE_LOSE   = "lose"

# Palet warna
C_BG           = ( 28,  34,  42)
C_CELL         = ( 40,  50,  60)
C_GRID_LINE    = ( 55,  65,  75)
C_PATH         = ( 60, 110, 170)
C_SPAWN        = (  0, 190,  90)
C_BASE         = (255, 160,   0)
C_BLOCKED      = (200,  40,  40)
C_HUD_TEXT     = (210, 210, 210)
C_HUD_WARN     = (255, 100, 100)
C_PANEL        = ( 20,  26,  34)
C_WIN          = ( 50, 200, 100)
C_LOSE         = (200,  50,  50)
C_OVERLAY      = (  0,   0,   0, 170)


# ─────────────────────────────────────────────
#  CLASS GAME
# ─────────────────────────────────────────────
class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("Algorithmic Tower Defense  |  BFS Pathfinding")
        self.clock  = pygame.time.Clock()

        self.font      = pygame.font.SysFont("consolas", 13)
        self.font_bold = pygame.font.SysFont("consolas", 15, bold=True)

        # ── Grid ──────────────────────────────
        # 0 = dapat dilalui,  1 = tower / rintangan
        self.grid = [[0] * COLS for _ in range(ROWS)]

        # ── Game objects ──────────────────────
        self.towers  = []
        self.enemies = []

        # ── Game State ────────────────────────
        # Fase saat ini: prep → (battle atau win) → lose
        self.state = STATE_PREP

        # Timer hitungan mundur Preparation Phase
        self.timer = Timer(PREP_DURATION, FPS)

        # ── Battle counters ───────────────────
        self.spawn_timer   = 0
        self.enemies_lost  = 0   # musuh yang berhasil mencapai Base

        # Hitung jalur awal (grid kosong → lurus horizontal)
        self.current_path = find_shortest_path(self.grid, SPAWN, BASE, ROWS, COLS)

    # ──────────────────────────────────────────
    #  EVENT HANDLING
    # ──────────────────────────────────────────
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                # R = restart dari awal (berlaku di semua state)
                if event.key == pygame.K_r:
                    self._restart()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Tower hanya bisa dipasang saat Preparation Phase
                if self.state == STATE_PREP:
                    mx, my = pygame.mouse.get_pos()
                    gx = mx // CELL_SIZE
                    gy = my // CELL_SIZE
                    self.try_place_tower(gx, gy)

    # ──────────────────────────────────────────
    #  RESTART
    # ──────────────────────────────────────────
    def _restart(self):
        """Reset semua state ke kondisi awal (Preparation Phase)."""
        self.grid        = [[0] * COLS for _ in range(ROWS)]
        self.towers      = []
        self.enemies     = []
        self.state       = STATE_PREP
        self.timer.reset(PREP_DURATION)
        self.spawn_timer = 0
        self.enemies_lost = 0
        self.current_path = find_shortest_path(self.grid, SPAWN, BASE, ROWS, COLS)

    # ──────────────────────────────────────────
    #  PENEMPATAN TOWER (+ VALIDASI BFS)
    # ──────────────────────────────────────────
    def try_place_tower(self, gx, gy):
        """
        Meletakkan tower di sel (gx, gy).

        Validasi:
        1. Pastikan bukan di Spawn / Base.
        2. Pastikan sel belum terisi tower.
        3. Simpan tower; perbarui jalur BFS jika masih ada.
        """
        # Guard: batas layar
        if not (0 <= gx < COLS and 0 <= gy < ROWS):
            return
        # Guard: jangan timpa Spawn / Base
        if (gx, gy) == SPAWN or (gx, gy) == BASE:
            return
        # Guard: sudah ada tower
        if self.grid[gy][gx] == 1:
            return

        # Pasang tower
        self.grid[gy][gx] = 1
        self.towers.append(Tower(gx, gy, CELL_SIZE))

        # Perbarui jalur BFS (bisa None jika semua jalur terblokir)
        new_path = find_shortest_path(self.grid, SPAWN, BASE, ROWS, COLS)
        self.current_path = new_path

        # Dynamic rerouting: perbarui jalur semua musuh aktif
        for enemy in self.enemies:
            enemy.set_path(self.current_path)

    # ──────────────────────────────────────────
    #  SPAWN MUSUH
    # ──────────────────────────────────────────
    def spawn_enemy(self):
        """Hasilkan musuh baru di SPAWN dengan jalur BFS terkini."""
        path = find_shortest_path(self.grid, SPAWN, BASE, ROWS, COLS)
        if path:
            self.enemies.append(Enemy(SPAWN, CELL_SIZE, path))

    # ──────────────────────────────────────────
    #  UPDATE (LOGIC)
    # ──────────────────────────────────────────
    def update(self):
        # ── PREPARATION PHASE ─────────────────
        if self.state == STATE_PREP:
            self.timer.update()

            # Timer habis → jalankan Reachability Check BFS
            if self.timer.finished:
                self._evaluate_reachability()
            return

        # ── BATTLE PHASE ──────────────────────
        if self.state == STATE_BATTLE:
            # Spawn musuh secara berkala
            self.spawn_timer += 1
            if self.spawn_timer >= ENEMY_SPAWN_INTERVAL:
                self.spawn_timer = 0
                self.spawn_enemy()

            # Update pergerakan semua musuh
            for enemy in self.enemies:
                enemy.update()

            # Cek musuh yang mencapai Base → LOSE
            reached = [e for e in self.enemies if e.reached_base]
            if reached:
                self.enemies_lost += len(reached)
                self.state = STATE_LOSE
                return

            # Hapus musuh yang sudah selesai
            self.enemies = [e for e in self.enemies if not e.reached_base and e.alive]

    # ──────────────────────────────────────────
    #  REACHABILITY CHECK (akhir Preparation Phase)
    # ──────────────────────────────────────────
    def _evaluate_reachability(self):
        """
        Dijalankan tepat saat timer Preparation Phase habis.

        Logika BFS Reachability (sesuai syarat Quiz 2):
        - Jalankan BFS dari SPAWN ke BASE pada grid yang sudah diisi tower.
        - Jika node BASE tidak pernah masuk queue / tidak pernah di-visited
          → Base tidak dapat dijangkau → PLAYER WIN.
        - Jika BFS berhasil menemukan jalur ke BASE
          → Base bisa dijangkau → transisi ke BATTLE PHASE.
        """
        path_exists = is_path_exists(self.grid, SPAWN, BASE, ROWS, COLS)

        if not path_exists:
            # BFS: Base tidak reachable → MENANG!
            self.state = STATE_WIN
        else:
            # BFS: jalur masih ada → musuh akan menyerang → BATTLE
            self.current_path = find_shortest_path(self.grid, SPAWN, BASE, ROWS, COLS)
            self.state = STATE_BATTLE

    # ──────────────────────────────────────────
    #  RENDERING
    # ──────────────────────────────────────────
    def draw_grid(self):
        """
        Render setiap sel grid dengan warna berbeda:
          - Biru  : jalur BFS saat ini
          - Hijau : Spawn
          - Oranye: Base
          - Default: warna latar sel biasa
        """
        path_set = set(self.current_path) if self.current_path else set()

        for row in range(ROWS):
            for col in range(COLS):
                rect = pygame.Rect(col * CELL_SIZE, row * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                pos  = (col, row)

                if pos == SPAWN:
                    pygame.draw.rect(self.screen, C_SPAWN, rect)
                elif pos == BASE:
                    pygame.draw.rect(self.screen, C_BASE, rect)
                elif self.grid[row][col] == 1:
                    pygame.draw.rect(self.screen, C_CELL, rect)   # tower akan digambar di atas
                elif pos in path_set:
                    pygame.draw.rect(self.screen, C_PATH, rect)
                else:
                    pygame.draw.rect(self.screen, C_CELL, rect)

                # Garis grid
                pygame.draw.rect(self.screen, C_GRID_LINE, rect, 1)

        # Label S / B
        def label(text, col, row, color=(0, 0, 0)):
            lbl = self.font_bold.render(text, True, color)
            self.screen.blit(lbl, (col * CELL_SIZE + CELL_SIZE // 2 - lbl.get_width() // 2,
                                   row * CELL_SIZE + CELL_SIZE // 2 - lbl.get_height() // 2))

        label("S", *SPAWN)
        label("B", *BASE)

    def draw_hud(self):
        """Render panel informasi di pojok kiri atas (konten sesuai fase)."""
        if self.state == STATE_PREP:
            lines = [
                ("Tower Defense  —  BFS Pathfinding", C_HUD_TEXT, True),
                (f"[ PREPARATION PHASE ]", C_WIN, True),
                (f"Waktu tersisa : {self.timer.seconds_left()}s", C_HUD_TEXT, False),
                (f"Towers        : {len(self.towers)}", C_HUD_TEXT, False),
                ("", C_HUD_TEXT, False),
                ("Klik sel kosong = pasang tower", C_HUD_TEXT, False),
                ("Blokir SEMUA jalur untuk menang!", C_WIN, False),
            ]
        elif self.state == STATE_BATTLE:
            lines = [
                ("Tower Defense  —  BFS Pathfinding", C_HUD_TEXT, True),
                (f"[ BATTLE PHASE ]", C_HUD_WARN, True),
                (f"Enemies aktif  : {len(self.enemies)}", C_HUD_TEXT, False),
                (f"Reached Base   : {self.enemies_lost}", C_HUD_WARN if self.enemies_lost else C_HUD_TEXT, False),
                ("", C_HUD_TEXT, False),
                ("Musuh menuju Base!", C_HUD_WARN, False),
            ]
        else:
            lines = [
                ("Tower Defense  —  BFS Pathfinding", C_HUD_TEXT, True),
                (f"Towers  : {len(self.towers)}", C_HUD_TEXT, False),
            ]

        pad = 8
        bg  = pygame.Surface((270, len(lines) * 17 + pad * 2), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 140))
        self.screen.blit(bg, (0, 0))

        for i, (text, color, bold) in enumerate(lines):
            font = self.font_bold if bold else self.font
            lbl  = font.render(text, True, color)
            self.screen.blit(lbl, (pad, pad + i * 17))

    # ──────────────────────────────────────────
    #  OVERLAY WIN / LOSE
    # ──────────────────────────────────────────
    def draw_overlay(self):
        """Render layar Win atau Lose di atas game."""
        if self.state not in (STATE_WIN, STATE_LOSE):
            return

        # Layer transparan gelap
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        self.screen.blit(overlay, (0, 0))

        font_big   = pygame.font.SysFont("consolas", 64, bold=True)
        font_small = pygame.font.SysFont("consolas", 22)

        if self.state == STATE_WIN:
            title_text = "YOU WIN!"
            title_color = C_WIN
            sub_text = "BFS: Base tidak dapat dijangkau musuh."
            sub_color = (180, 255, 180)
        else:
            title_text = "YOU LOSE"
            title_color = C_LOSE
            sub_text = f"Musuh berhasil mencapai Base!"
            sub_color = (255, 180, 180)

        title = font_big.render(title_text, True, title_color)
        sub   = font_small.render(sub_text, True, sub_color)
        hint  = font_small.render("Tekan R untuk main lagi", True, C_HUD_TEXT)

        cx = SCREEN_W // 2
        cy = SCREEN_H // 2
        self.screen.blit(title, (cx - title.get_width() // 2, cy - 80))
        self.screen.blit(sub,   (cx - sub.get_width() // 2,   cy + 10))
        self.screen.blit(hint,  (cx - hint.get_width() // 2,  cy + 55))

    # ──────────────────────────────────────────
    #  PREP PHASE TIMER BAR
    # ──────────────────────────────────────────
    def draw_timer_bar(self):
        """Bar hitungan mundur di bagian bawah layar (hanya saat PREP)."""
        if self.state != STATE_PREP:
            return
        bar_w  = int(SCREEN_W * (1.0 - self.timer.progress()))
        bar_h  = 8
        bar_y  = SCREEN_H - bar_h
        # Background
        pygame.draw.rect(self.screen, (50, 50, 60), (0, bar_y, SCREEN_W, bar_h))
        # Bar: hijau → merah seiring waktu habis
        ratio   = 1.0 - self.timer.progress()
        r_val   = int(255 * (1 - ratio))
        g_val   = int(255 * ratio)
        pygame.draw.rect(self.screen, (r_val, g_val, 40), (0, bar_y, bar_w, bar_h))

    # ──────────────────────────────────────────
    #  GAME LOOP UTAMA
    # ──────────────────────────────────────────
    def run(self):
        while True:
            self.handle_events()
            self.update()

            self.screen.fill(C_BG)

            self.draw_grid()

            for tower in self.towers:
                tower.draw(self.screen)

            for enemy in self.enemies:
                enemy.draw(self.screen)

            self.draw_hud()
            self.draw_timer_bar()
            self.draw_overlay()   # WIN / LOSE screen (hanya saat state terkait)

            pygame.display.flip()
            self.clock.tick(FPS)


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    game = Game()
    game.run()
