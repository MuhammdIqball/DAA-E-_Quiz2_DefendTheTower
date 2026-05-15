"""
main.py
=======
Entry point game Tower Defense berbasis algoritma BFS.

Tanggung jawab modul ini:
- Inisialisasi Pygame & window
- Game loop utama (handle event → update → render)
- Penanganan klik mouse (penempatan tower + validasi BFS)
- Rendering grafis (grid, path, entities, HUD)

Pembagian modul:
  main.py         → (file ini)  inisialisasi, loop, event, render
  pathfinding.py  → logika graf, algoritma BFS
  entities.py     → class Tower dan Enemy
"""

import pygame
import sys

from pathfinding import find_shortest_path
from entities import Tower, Enemy

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
ENEMY_SPAWN_INTERVAL = 150   # frame antar spawn musuh

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

        # ── State ─────────────────────────────
        self.spawn_timer   = 0
        self.enemies_lost  = 0   # musuh yang berhasil mencapai Base

        # Flash merah saat penempatan tower ditolak
        self.flash_timer = 0
        self.flash_cell  = None

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

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = pygame.mouse.get_pos()
                gx = mx // CELL_SIZE
                gy = my // CELL_SIZE
                self.try_place_tower(gx, gy)

    # ──────────────────────────────────────────
    #  PENEMPATAN TOWER (+ VALIDASI BFS)
    # ──────────────────────────────────────────
    def try_place_tower(self, gx, gy):
        """
        Mencoba meletakkan tower di sel (gx, gy).

        Proses validasi (WAJIB sesuai spesifikasi):
        1. Pastikan bukan di Spawn / Base.
        2. Pastikan sel belum terisi tower.
        3. Tandai sementara sebagai rintangan (grid = 1).
        4. Jalankan BFS: jika TIDAK ADA jalur → TOLAK, revert grid.
        5. Jika valid → simpan tower, perbarui jalur semua musuh aktif.
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

        # ── Langkah 3: simulasi penempatan ──
        self.grid[gy][gx] = 1

        # ── Langkah 4: validasi jalur dengan BFS ──
        test_path = find_shortest_path(self.grid, SPAWN, BASE, ROWS, COLS)

        if test_path is None:
            # Penempatan memutus semua jalur → TOLAK
            self.grid[gy][gx] = 0          # revert
            self.flash_cell  = (gx, gy)
            self.flash_timer = 35          # frame efek merah
            return

        # ── Langkah 5: penempatan valid ──
        self.towers.append(Tower(gx, gy, CELL_SIZE))
        self.current_path = test_path

        # Dynamic rerouting: perbarui jalur SEMUA musuh yang sedang berjalan
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
        # Timer spawn musuh
        self.spawn_timer += 1
        if self.spawn_timer >= ENEMY_SPAWN_INTERVAL:
            self.spawn_timer = 0
            self.spawn_enemy()

        # Kurangi flash timer
        if self.flash_timer > 0:
            self.flash_timer -= 1
        else:
            self.flash_cell = None

        # Update pergerakan semua musuh
        for enemy in self.enemies:
            enemy.update()

        # Hapus musuh yang sudah mencapai Base
        reached = [e for e in self.enemies if e.reached_base]
        self.enemies_lost += len(reached)
        self.enemies = [e for e in self.enemies if not e.reached_base and e.alive]

    # ──────────────────────────────────────────
    #  RENDERING
    # ──────────────────────────────────────────
    def draw_grid(self):
        """
        Render setiap sel grid dengan warna berbeda:
          - Biru  : jalur BFS saat ini
          - Hijau : Spawn
          - Oranye: Base
          - Merah : penolakan tower (flash sementara)
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
                elif self.flash_cell == pos:
                    # Efek flash merah → penempatan ditolak
                    alpha  = int(255 * self.flash_timer / 35)
                    flash  = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
                    flash.fill((*C_BLOCKED, alpha))
                    pygame.draw.rect(self.screen, C_CELL, rect)
                    self.screen.blit(flash, rect.topleft)
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
        """Render panel informasi di pojok kiri atas."""
        lines = [
            ("Tower Defense  —  BFS Pathfinding", C_HUD_TEXT, True),
            (f"Towers   : {len(self.towers)}", C_HUD_TEXT, False),
            (f"Enemies  : {len(self.enemies)}", C_HUD_TEXT, False),
            (f"Reached  : {self.enemies_lost}", C_HUD_WARN if self.enemies_lost else C_HUD_TEXT, False),
            ("", C_HUD_TEXT, False),
            ("Klik sel kosong = pasang tower", C_HUD_TEXT, False),
            ("Tower merah = jalur terblokir (ditolak)", C_HUD_WARN, False),
        ]

        pad = 8
        bg  = pygame.Surface((230, len(lines) * 17 + pad * 2), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 120))
        self.screen.blit(bg, (0, 0))

        for i, (text, color, bold) in enumerate(lines):
            font = self.font_bold if bold else self.font
            lbl  = font.render(text, True, color)
            self.screen.blit(lbl, (pad, pad + i * 17))

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

            pygame.display.flip()
            self.clock.tick(FPS)


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    game = Game()
    game.run()
