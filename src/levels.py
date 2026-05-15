"""
levels.py
=========
Konfigurasi grid untuk setiap level.

Nilai sel grid:
  0 = kosong          (traversable oleh musuh, buildable oleh pemain)
  1 = obstacle/tower  (NOT traversable, NOT buildable)
  2 = no-build zone   (traversable oleh musuh, NOT buildable oleh pemain)

No-build zones direpresentasikan sebagai "rawa" atau "hutan" yang bisa
dilalui musuh tetapi tidak bisa dibangun rintangan di atasnya.
Ini memaksa pemain mencari cut-set di area yang lebih terbatas.
"""

COLS = 20
ROWS = 15


def _rect(col_start, col_end, row_start, row_end):
    """Buat set koordinat (col, row) dari rentang persegi panjang."""
    return {
        (c, r)
        for r in range(row_start, row_end + 1)
        for c in range(col_start, col_end + 1)
    }


# ─────────────────────────────────────────────
#  LEVEL 1 — No-Build Zone di dekat BASE (kanan)
# ─────────────────────────────────────────────
# Rawa di pojok kanan-atas dan kanan-bawah.
# Musuh BISA lewat, pemain TIDAK BISA bangun di area ini.
# Tujuan: pemain harus memblokir di area tengah/kiri (cols 1–14).
_L1_NO_BUILD = (
    _rect(15, 18,  0,  4) |   # rawa kanan-atas
    _rect(15, 18, 10, 14)     # rawa kanan-bawah
)

# ─────────────────────────────────────────────
#  LEVEL 2 — No-Build Zone di KEDUA sisi (lebih sulit)
# ─────────────────────────────────────────────
# Tambah rawa di pojok kiri (dekat SPAWN) — area buildable makin sempit.
# Pemain HARUS memblokir di kolom 5–14 saja.
_L2_NO_BUILD = (
    _L1_NO_BUILD              |   # semua rawa Level 1
    _rect( 1,  4,  0,  4)    |   # rawa kiri-atas
    _rect( 1,  4, 10, 14)        # rawa kiri-bawah
)

# Level 2: dinding parsial bawaan di kolom 9 (atas & bawah)
# Menciptakan "funnel" — musuh harus lewat baris 3–11 di col 9.
# Membuat cut-set lebih sulit ditemukan.
_L2_PRE_OBSTACLES = [
    *[(9, r) for r in range(0, 3)],    # col 9, baris 0–2
    *[(9, r) for r in range(12, 15)],  # col 9, baris 12–14
]

# ─────────────────────────────────────────────
#  REGISTRY LEVEL
# ─────────────────────────────────────────────
LEVEL_CONFIGS = {
    1: {
        "name"          : "Level 1",
        "spawn"         : (0,  7),
        "base"          : (19, 7),
        "prep_duration" : 20,
        "no_build_zones": _L1_NO_BUILD,
        "pre_obstacles" : [],
    },
    2: {
        "name"          : "Level 2",
        "spawn"         : (0,  7),
        "base"          : (19, 7),
        "prep_duration" : 25,
        "no_build_zones": _L2_NO_BUILD,
        "pre_obstacles" : _L2_PRE_OBSTACLES,
    },
}

MAX_LEVEL = max(LEVEL_CONFIGS.keys())


def build_grid(level_num):
    """
    Bangun grid ROWS×COLS untuk level yang diberikan.

    Kembalian:
    ----------
    list[list[int]]: grid[row][col]
        0 = kosong
        1 = pre-placed obstacle
        2 = no-build zone
    """
    cfg  = LEVEL_CONFIGS[level_num]
    grid = [[0] * COLS for _ in range(ROWS)]

    # Pasang no-build zones (nilai 2)
    for (col, row) in cfg["no_build_zones"]:
        if 0 <= row < ROWS and 0 <= col < COLS:
            grid[row][col] = 2

    # Pasang pre-placed obstacles (nilai 1)
    for (col, row) in cfg["pre_obstacles"]:
        if 0 <= row < ROWS and 0 <= col < COLS:
            grid[row][col] = 1

    return grid
