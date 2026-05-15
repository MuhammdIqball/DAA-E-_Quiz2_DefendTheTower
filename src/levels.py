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
#  LEVEL 1 — "Introduction"
#  Dinding vertikal di col 9, CELAH hanya di row 2 (dekat atas).
#  Jalur dari Spawn (0,7) HARUS naik ke row 2, menyeberang, lalu turun ke Base.
#  Menghasilkan jalur melengkung (arc) yang intuitif bagi pemain baru.
#  Solusi: blokir (9, 2)  →  1 blok.
# =============================================================================
_L1_PRE = [(9, r) for r in range(ROWS) if r != 2]

# =============================================================================
#  LEVEL 2 — "The False Shortcut"
#  Tembok tebal (3 baris) memblokir sebagian besar grid, meninggalkan:
#    - PATH A: row 7 terbuka penuh (jalur lurus yang SANGAT JELAS).
#    - PATH B: top/bottom band (rows 0–3 dan 11–14) + col 12 sebagai konektor.
#  Col 12 (rows 4–10) = SATU KOLOM TERBUKA yang menghubungkan band atas/bawah
#  ke row 7. Titik pertemuan kedua jalur = (12, 7).
#
#  UNSUR KECOH: Pemain insting blokir di tengah row 7 (mis. (6,7) atau (9,7)).
#  Namun Path B dari top/bottom masih lewat col 12 → (12,7) → Base. Satu-satunya
#  titik yang memutus KEDUANYA adalah (12, 7).
#
#  Solusi: blokir (12, 7)  →  1 blok.
# =============================================================================
_L2_PRE = (
    [(c, r) for r in range(4, 7)  for c in range(1,  12)] +  # rows 4-6,  cols 1-11
    [(c, r) for r in range(4, 7)  for c in range(13, 20)] +  # rows 4-6,  cols 13-19
    [(c, r) for r in range(8, 11) for c in range(1,  12)] +  # rows 8-10, cols 1-11
    [(c, r) for r in range(8, 11) for c in range(13, 20)]    # rows 8-10, cols 13-19
)

# =============================================================================
#  LEVEL 3 — "The Spider Web"
#  Dua dinding vertikal dengan celah di KETINGGIAN SAMA:
#    - Wall A: col  7, celah di row 3 DAN row 11
#    - Wall B: col 13, celah di row 3 DAN row 11
#  Zona tengah (cols 8-12) terlihat kompleks karena dekorasi "web" (obstacles
#  berbentuk sarang laba-laba di col 10 + baris 6 & 8).
#
#  EMPAT jalur yang ada:
#    (7,3)→(13,3)  : top-straight
#    (7,11)→(13,11): bottom-straight
#    (7,3)→(13,11) : top-cross   (lewat tengah)
#    (7,11)→(13,3) : bottom-cross (lewat tengah)
#
#  UNSUR KECOH: Pemain sering blokir satu celah dari masing-masing dinding
#  (mis. (7,3) + (13,11)) — tapi ini TIDAK cukup karena jalur silang masih ada!
#  Solusi: HARUS blokir KEDUA celah dari SATU dinding yang sama.
#
#  Solusi valid:
#    (7,3)  + (7,11)   → potong Wall A sepenuhnya
#    (13,3) + (13,11)  → potong Wall B sepenuhnya
#  →  2 blok.
# =============================================================================
_L3_WALL_A = [(7,  r) for r in range(ROWS) if r not in (3, 11)]
_L3_WALL_B = [(13, r) for r in range(ROWS) if r not in (3, 11)]
# Dekorasi "web" di zona tengah — menambah kompleksitas visual, bukan bottleneck
_L3_WEB = [
    (10, 0), (10, 1), (10, 2),          # top stem
    ( 9, 6), (10, 6), (11, 6),          # horizontal bar atas row 7
    ( 9, 8), (10, 8), (11, 8),          # horizontal bar bawah row 7
    (10, 12), (10, 13), (10, 14),       # bottom stem
]
_L3_PRE = _L3_WALL_A + _L3_WALL_B + _L3_WEB

# =============================================================================
#  REGISTRY LEVEL
# =============================================================================
LEVEL_CONFIGS = {
    1: {
        "name"          : "Level 1 — Introduction",
        "hint"          : "Jalur naik dulu, baru ke Base. Temukan celah di dinding!",
        "spawn"         : (0,  7),
        "base"          : (19, 7),
        "block_count"   : 1,
        "pre_obstacles" : _L1_PRE,
        "no_build_zones": set(),
    },
    2: {
        "name"          : "Level 2 — The False Shortcut",
        "hint"          : "Ada jalan lurus... dan jalan tersembunyi. Cari titik temu keduanya!",
        "spawn"         : (0,  7),
        "base"          : (19, 7),
        "block_count"   : 1,
        "pre_obstacles" : _L2_PRE,
        "no_build_zones": set(),
    },
    3: {
        "name"          : "Level 3 — The Spider Web",
        "hint"          : "Dua tembok, empat celah. Potong satu tembok PENUH — jangan lintas!",
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
