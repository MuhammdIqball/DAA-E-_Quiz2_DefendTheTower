"""
pathfinding.py
==============
Modul khusus logika Graf dan algoritma pencarian jalur (pathfinding).
Mengimplementasikan Breadth-First Search (BFS) pada grid 2D.

Kenapa BFS?
- Semua edge pada grid ini memiliki bobot yang sama (setiap langkah = 1).
- BFS menjamin jalur terpendek (dalam jumlah langkah) pada graf tak berbobot.
- Kompleksitas waktu: O(V + E) = O(ROWS * COLS) per panggilan.
"""

from collections import deque


def find_shortest_path(grid, start, end, rows, cols):
    """
    Mencari jalur terpendek dari `start` ke `end` menggunakan BFS.

    Parameter:
    ----------
    grid  : list[list[int]]
        Representasi matriks 2D dari peta.
        0 = sel yang bisa dilewati (passable)
        1 = rintangan / tower (impassable)
    start : tuple(int, int)
        Posisi awal dalam format (col, row).
    end   : tuple(int, int)
        Posisi tujuan dalam format (col, row).
    rows  : int
        Jumlah baris pada grid.
    cols  : int
        Jumlah kolom pada grid.

    Kembalian:
    ----------
    list[tuple(int, int)] | None
        Daftar posisi (col, row) yang membentuk jalur terpendek dari start ke end,
        termasuk start dan end. Mengembalikan None jika tidak ada jalur.
    """

    # Guard: titik awal atau akhir sendiri adalah rintangan
    if grid[start[1]][start[0]] == 1 or grid[end[1]][end[0]] == 1:
        return None

    # --- Inisialisasi BFS ---
    # Queue BFS: setiap elemen adalah posisi grid (col, row) yang akan dikunjungi
    queue = deque()
    queue.append(start)

    # Dictionary 'visited' berfungsi ganda:
    # 1. Mencatat sel yang sudah dikunjungi (mencegah loop)
    # 2. Menyimpan "parent" setiap sel untuk rekonstruksi jalur
    # Format: { node: parent_node }, node awal memiliki parent None
    visited = {start: None}

    # Arah pergerakan: atas, bawah, kiri, kanan (4-directional)
    directions = [(0, -1), (0, 1), (-1, 0), (1, 0)]

    # --- Loop Utama BFS ---
    while queue:
        current = queue.popleft()  # Ambil node terdepan dari antrian

        # Jika sudah sampai di tujuan, rekonstruksi jalur
        if current == end:
            path = []
            node = end
            # Lacak balik dari end ke start menggunakan parent pointer
            while node is not None:
                path.append(node)
                node = visited[node]
            path.reverse()  # Balik agar urutan dari start -> end
            return path

        cx, cy = current
        # Eksplorasi semua tetangga (atas, bawah, kiri, kanan)
        for dx, dy in directions:
            nx, ny = cx + dx, cy + dy
            # Cek batas grid
            if 0 <= nx < cols and 0 <= ny < rows:
                # Masukkan ke antrian hanya jika belum dikunjungi DAN bisa dilewati
                if (nx, ny) not in visited and grid[ny][nx] != 1:
                    visited[(nx, ny)] = current  # Catat parent
                    queue.append((nx, ny))

    # Antrian habis tanpa menemukan end -> tidak ada jalur
    return None


def is_path_exists(grid, start, end, rows, cols):
    """
    Cek cepat apakah jalur dari start ke end masih ada.
    Digunakan untuk validasi sebelum penempatan tower.

    Kembalian:
    ----------
    bool : True jika jalur ada, False jika terblokir total.
    """
    return find_shortest_path(grid, start, end, rows, cols) is not None
