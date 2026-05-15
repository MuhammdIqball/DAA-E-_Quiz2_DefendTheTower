"""
levels.py  (Puzzle Mode)
========================
Konfigurasi setiap level sebagai PUZZLE BOTTLENECK.

Representasi graf:
  Sel = node,  edge antara sel bertetangga (4-arah) yang bisa dilalui.

Nilai sel grid:
  0 = kosong          (traversable, buildable oleh pemain)
  1 = obstacle tetap  (NOT traversable, NOT buildable)
  2 = no-build zone   (traversable oleh musuh, NOT buildable)

Setiap level memiliki:
  - pre_obstacles : rintangan permanen yang membentuk "funnel" / bottleneck
  - block_count   : jumlah blok yang BOLEH dipasang pemain
  - hint          : teks petunjuk yang ditampilkan di HUD

Pemain menang  → Dijkstra mengembalikan None (tidak ada jalur).
Pemain kalah   → Dijkstra masih menemukan jalur setelah semua blok habis.
"""

COLS = 20
ROWS = 15

# =============================================================================
#  LEVEL 1 — "The Gateway"
#  Satu dinding vertikal di col 9, satu celah di row 7 (tepat di tengah).
#  Semua jalur HARUS melewati (9, 7).
#  Solusi: blokir (9, 7)  →  1 blok.
# =============================================================================
_L1_PRE = [(9, r) for r in range(ROWS) if r != 7]

# =============================================================================
#  LEVEL 2 — "Twin Gaps"
#  Dinding vertikal di col 9, dua celah di row 3 dan row 11.
#  Jalur atas melewati (9, 3); jalur bawah melewati (9, 11).
#  Solusi: blokir keduanya  →  2 blok.
# =============================================================================
_L2_PRE = [(9, r) for r in range(ROWS) if r not in (3, 11)]

# =============================================================================
#  LEVEL 3 — "The Crossroads"
#  Dua dinding vertikal di col 6 dan col 13.
#    - Col  6: satu celah di row 4
#    - Col 13: satu celah di row 10
#  Bottleneck berada di ketinggian BERBEDA — jalur harus zig-zag.
#  Solusi: blokir (6, 4) DAN (13, 10)  →  2 blok.
# =============================================================================
_L3_PRE = (
    [(6,  r) for r in range(ROWS) if r != 4] +
    [(13, r) for r in range(ROWS) if r != 10]
)

# =============================================================================
#  REGISTRY LEVEL
# =============================================================================
LEVEL_CONFIGS = {
    1: {
        "name"          : "Level 1 — The Gateway",
        "hint"          : "Satu dinding, satu celah. Tutup celah itu!",
        "spawn"         : (0,  7),
        "base"          : (19, 7),
        "block_count"   : 1,
        "pre_obstacles" : _L1_PRE,
        "no_build_zones": set(),
    },
    2: {
        "name"          : "Level 2 — Twin Gaps",
        "hint"          : "Dua celah di dinding. Butuh 2 blok untuk menutup keduanya.",
        "spawn"         : (0,  7),
        "base"          : (19, 7),
        "block_count"   : 2,
        "pre_obstacles" : _L2_PRE,
        "no_build_zones": set(),
    },
    3: {
        "name"          : "Level 3 — The Crossroads",
        "hint"          : "Dua dinding, celah di ketinggian berbeda. Temukan bottleneck!",
        "spawn"         : (0,  7),
        "base"          : (19, 7),
        "block_count"   : 2,
        "pre_obstacles" : _L3_PRE,
        "no_build_zones": set(),
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
      1 = obstacle permanen
      2 = no-build zone
    """
    cfg  = LEVEL_CONFIGS[level_num]
    grid = [[0] * COLS for _ in range(ROWS)]

    for (col, row) in cfg.get("no_build_zones", set()):
        if 0 <= row < ROWS and 0 <= col < COLS:
            grid[row][col] = 2

    for (col, row) in cfg["pre_obstacles"]:
        if 0 <= row < ROWS and 0 <= col < COLS:
            grid[row][col] = 1

    return grid
