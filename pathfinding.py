"""
pathfinding.py
==============
Modul khusus logika Graf dan algoritma pencarian jalur (pathfinding).
Mengimplementasikan dua algoritma:
  - BFS  (Breadth-First Search)   : digunakan untuk update jalur real-time saat drag
  - Dijkstra                       : digunakan untuk evaluasi solusi puzzle (win/lose check)

Kenapa BFS untuk real-time?
- O(V+E) tanpa overhead priority queue → lebih cepat untuk update tiap blok yang dipasang.
Kenapa Dijkstra untuk evaluasi?
- Memenuhi syarat DAA Quiz 2; pada grid uniform hasilnya identik dengan BFS
  tetapi menggunakan priority queue (min-heap) sesuai definisi algoritma Dijkstra.
- Kompleksitas: O((V + E) log V) = O(ROWS * COLS * log(ROWS * COLS)).
"""

from collections import deque
import heapq


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


def dijkstra(grid, start, end, rows, cols):
    """
    Mencari jalur terpendek menggunakan algoritma Dijkstra dengan min-heap.

    Digunakan untuk evaluasi solusi puzzle (win/lose check) sesuai syarat DAA Quiz 2.
    Pada grid 2D uniform (semua edge berbobot 1), hasil identik dengan BFS
    tetapi menggunakan priority queue untuk mendemonstrasikan algoritma Dijkstra.

    Parameter:
    ----------
    grid  : list[list[int]]
        0 / 2 = traversable,  1 = obstacle (NOT traversable).
    start : tuple(int, int) - posisi (col, row) awal.
    end   : tuple(int, int) - posisi (col, row) tujuan.
    rows  : int
    cols  : int

    Kembalian:
    ----------
    list[tuple(int, int)] | None
        Jalur terpendek dari start ke end, atau None jika tidak ada.
    """
    # Guard: titik awal / akhir adalah dinding
    if grid[start[1]][start[0]] == 1 or grid[end[1]][end[0]] == 1:
        return None

    # --- Inisialisasi Dijkstra ---
    # dist: biaya minimum untuk mencapai setiap sel
    # Semua sel diinisialisasi tak-hingga kecuali titik awal (cost = 0)
    dist   = {start: 0}
    # parent: untuk rekonstruksi jalur balik
    parent = {start: None}
    # Min-heap priority queue: elemen = (cost, col, row)
    heap   = [(0, start[0], start[1])]

    directions = [(0, -1), (0, 1), (-1, 0), (1, 0)]

    # --- Loop Utama Dijkstra ---
    while heap:
        cost, cx, cy = heapq.heappop(heap)  # ambil node dengan cost terkecil
        current = (cx, cy)

        # Early exit saat tujuan tercapai
        if current == end:
            # Rekonstruksi jalur balik dari end ke start
            path = []
            node = end
            while node is not None:
                path.append(node)
                node = parent[node]
            path.reverse()  # balik agar start → end
            return path

        # Lewati entri lama di heap (stale / sudah ada jalur lebih pendek)
        if cost > dist.get(current, float('inf')):
            continue

        for dx, dy in directions:
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < cols and 0 <= ny < rows:
                # Hanya lewati sel yang bukan dinding (nilai 1)
                # Sel no-build zone (nilai 2) BISA dilewati musuh
                if grid[ny][nx] != 1:
                    new_cost = cost + 1  # setiap langkah berbobot 1
                    neighbor = (nx, ny)
                    # Relaxation: perbarui jika ditemukan jalur lebih pendek
                    if new_cost < dist.get(neighbor, float('inf')):
                        dist[neighbor]   = new_cost
                        parent[neighbor] = current
                        heapq.heappush(heap, (new_cost, nx, ny))

    # Heap kosong, end tidak tercapai → tidak ada jalur
    return None
