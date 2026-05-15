"""
entities.py
===========
Berisi class Tower dan Enemy untuk game Tower Defense.
"""

import pygame
import math


class Tower:
    """
    Tower: rintangan statis yang ditempatkan pemain di grid.
    Merepresentasikan obstacle yang menghalangi jalur musuh.
    """

    COLOR_BODY   = (70, 100, 200)   # Biru gelap
    COLOR_BORDER = (40,  60, 150)
    COLOR_TOP    = (120, 160, 255)  # Sorot atas

    def __init__(self, grid_x, grid_y, cell_size):
        self.grid_x    = grid_x
        self.grid_y    = grid_y
        self.cell_size = cell_size

    def draw(self, surface):
        cs = self.cell_size
        x  = self.grid_x * cs
        y  = self.grid_y * cs

        # Badan tower
        body_rect = pygame.Rect(x + 4, y + 4, cs - 8, cs - 8)
        pygame.draw.rect(surface, self.COLOR_BODY, body_rect, border_radius=4)
        pygame.draw.rect(surface, self.COLOR_BORDER, body_rect, 2, border_radius=4)

        # Highlight atas (efek 3D sederhana)
        top_rect = pygame.Rect(x + 6, y + 6, cs - 12, 6)
        pygame.draw.rect(surface, self.COLOR_TOP, top_rect, border_radius=2)

        # Cannon (lingkaran kecil di tengah)
        cx = x + cs // 2
        cy = y + cs // 2
        pygame.draw.circle(surface, (200, 220, 255), (cx, cy), 5)
        pygame.draw.circle(surface, self.COLOR_BORDER, (cx, cy), 5, 1)


class Enemy:
    """
    Enemy: musuh yang bergerak mengikuti jalur terpendek dari Spawn ke Base.
    Direpresentasikan sebagai lingkaran merah.

    Pergerakan smooth dilakukan di level piksel, sedangkan logika jalur
    dikelola dalam koordinat grid.
    """

    COLOR_BODY   = (220,  50,  50)  # Merah
    COLOR_BORDER = (140,  20,  20)
    RADIUS       = 13
    SPEED        = 1.8  # Piksel per frame

    def __init__(self, spawn, cell_size, path=None):
        """
        Parameter:
        ----------
        spawn     : tuple(int, int)  - posisi grid awal (col, row)
        cell_size : int              - ukuran tiap sel dalam piksel
        path      : list[(col, row)] - jalur BFS awal dari pathfinding.py
        """
        self.grid_x    = spawn[0]
        self.grid_y    = spawn[1]
        self.cell_size = cell_size

        # Posisi piksel (center sel)
        self.pixel_x   = float(self.grid_x * cell_size + cell_size // 2)
        self.pixel_y   = float(self.grid_y * cell_size + cell_size // 2)

        self.path       = path if path else []
        self.path_index = 0  # Indeks target berikutnya dalam self.path

        self.alive        = True
        self.reached_base = False

    # ------------------------------------------------------------------
    def set_path(self, new_path):
        """
        Perbarui jalur musuh (dipanggil saat tower baru ditempatkan).

        Strategi: Cari node pada new_path yang paling dekat dengan posisi
        grid musuh saat ini, lanjutkan dari sana.
        Ini memastikan musuh tidak mundur dan langsung meneruskan
        perjalanan pada jalur baru.
        """
        if not new_path:
            self.path       = []
            self.path_index = 0
            return

        current_pos = (self.grid_x, self.grid_y)

        # Cari indeks terdekat pada new_path (jarak Manhattan)
        min_dist   = float('inf')
        best_index = 0
        for i, node in enumerate(new_path):
            dist = abs(node[0] - current_pos[0]) + abs(node[1] - current_pos[1])
            if dist < min_dist:
                min_dist   = dist
                best_index = i

        self.path       = new_path
        self.path_index = best_index

    # ------------------------------------------------------------------
    def update(self):
        """
        Gerakkan musuh selangkah menuju node berikutnya pada jalur.
        Saat sampai di node, grid_x/grid_y diperbarui dan path_index maju.
        """
        if not self.path or self.path_index >= len(self.path):
            return

        target_grid = self.path[self.path_index]
        cs          = self.cell_size
        target_px   = target_grid[0] * cs + cs // 2
        target_py   = target_grid[1] * cs + cs // 2

        dx   = target_px - self.pixel_x
        dy   = target_py - self.pixel_y
        dist = math.hypot(dx, dy)

        if dist <= self.SPEED:
            # Snap ke target, majukan ke node berikutnya
            self.pixel_x           = float(target_px)
            self.pixel_y           = float(target_py)
            self.grid_x, self.grid_y = target_grid
            self.path_index        += 1

            # Cek apakah sudah sampai di akhir jalur (Base)
            if self.path_index >= len(self.path):
                self.reached_base = True
        else:
            # Gerak smooth menuju target
            self.pixel_x += self.SPEED * dx / dist
            self.pixel_y += self.SPEED * dy / dist

    # ------------------------------------------------------------------
    def draw(self, surface):
        cx = int(self.pixel_x)
        cy = int(self.pixel_y)

        # Bayangan sederhana
        pygame.draw.circle(surface, (100, 20, 20), (cx + 2, cy + 2), self.RADIUS)
        # Badan
        pygame.draw.circle(surface, self.COLOR_BODY, (cx, cy), self.RADIUS)
        # Border
        pygame.draw.circle(surface, self.COLOR_BORDER, (cx, cy), self.RADIUS, 2)
        # Highlight kecil
        pygame.draw.circle(surface, (255, 140, 140), (cx - 4, cy - 4), 4)
