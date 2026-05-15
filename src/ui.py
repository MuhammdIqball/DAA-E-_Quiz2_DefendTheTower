"""
ui.py
=====
Komponen UI: Button, MainMenu, InstructionsScreen, LevelTransition.
"""

import pygame
import sys

SCREEN_W = 800
SCREEN_H = 600

# Palet UI
C_BG         = ( 28,  34,  42)
C_TITLE      = ( 50, 200, 100)
C_BTN_NORMAL = ( 50,  65,  80)
C_BTN_HOVER  = ( 70, 105, 140)
C_BTN_BORDER = (100, 145, 190)
C_BTN_TEXT   = (225, 225, 225)
C_TEXT       = (210, 210, 210)
C_MUTED      = (130, 150, 170)


class Button:
    """Tombol interaktif dengan efek hover."""

    def __init__(self, rect, text, font):
        self.rect    = pygame.Rect(rect)
        self.text    = text
        self.font    = font
        self.hovered = False

    def handle_event(self, event):
        """Kembalikan True jika tombol diklik kiri."""
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        return False

    def draw(self, surface):
        color = C_BTN_HOVER if self.hovered else C_BTN_NORMAL
        pygame.draw.rect(surface, color,        self.rect, border_radius=8)
        pygame.draw.rect(surface, C_BTN_BORDER, self.rect, 2, border_radius=8)
        lbl = self.font.render(self.text, True, C_BTN_TEXT)
        surface.blit(lbl, (
            self.rect.centerx - lbl.get_width()  // 2,
            self.rect.centery - lbl.get_height() // 2,
        ))


# ─────────────────────────────────────────────
#  MAIN MENU
# ─────────────────────────────────────────────
class MainMenu:
    """Layar utama: Start Game, Instructions, Exit."""

    def __init__(self, screen):
        self.screen     = screen
        self.font_title = pygame.font.SysFont("consolas", 48, bold=True)
        self.font_sub   = pygame.font.SysFont("consolas", 16)
        self.font_btn   = pygame.font.SysFont("consolas", 20, bold=True)

        cx = SCREEN_W // 2
        bw, bh = 260, 52
        self.btn_start = Button((cx - bw // 2, 250, bw, bh), "Start Game",    self.font_btn)
        self.btn_instr = Button((cx - bw // 2, 318, bw, bh), "Instructions",  self.font_btn)
        self.btn_exit  = Button((cx - bw // 2, 386, bw, bh), "Exit",          self.font_btn)

    def handle_event(self, event):
        """
        Kembalian:
          "start"        → mulai game dari Level 1
          "instructions" → buka layar instruksi
          "exit"         → keluar aplikasi
          None           → tidak ada aksi
        """
        if self.btn_start.handle_event(event): return "start"
        if self.btn_instr.handle_event(event): return "instructions"
        if self.btn_exit.handle_event(event):  return "exit"
        return None

    def draw(self):
        self.screen.fill(C_BG)

        title = self.font_title.render("Tower Defense", True, C_TITLE)
        self.screen.blit(title, (SCREEN_W // 2 - title.get_width() // 2, 110))

        sub = self.font_sub.render("BFS Pathfinding  |  DAA Quiz 2", True, C_MUTED)
        self.screen.blit(sub, (SCREEN_W // 2 - sub.get_width() // 2, 178))

        self.btn_start.draw(self.screen)
        self.btn_instr.draw(self.screen)
        self.btn_exit.draw(self.screen)


# ─────────────────────────────────────────────
#  INSTRUCTIONS SCREEN
# ─────────────────────────────────────────────
class InstructionsScreen:
    """Layar petunjuk cara bermain."""

    LINES = [
        ("CARA BERMAIN",                                         (50, 200, 100), True),
        ("",                                                     None,           False),
        ("PREPARATION PHASE:",                                   (180, 220, 255), False),
        ("  Drag klik kiri untuk membangun rintangan (obstacle)", C_TEXT,        False),
        ("  Tujuan: blokir SEMUA jalur dari Spawn ke Base",       (50,200,100),  False),
        ("  Area HIJAU     = Spawn (titik asal musuh)",           C_TEXT,        False),
        ("  Area ORANYE    = Base  (target musuh)",               C_TEXT,        False),
        ("  Area HIJAU TUA = No-Build Zone (rawa — bisa dilalui, tapi tak bisa dibangun)",
                                                                 (140,180,120),  False),
        ("",                                                     None,           False),
        ("BATTLE PHASE (saat timer habis):",                     (180, 220, 255), False),
        ("  BFS dijalankan: jika Base tidak reachable → MENANG", (50, 200, 100), False),
        ("  Jika jalur masih ada → musuh menyerang",             C_TEXT,        False),
        ("  Musuh mencapai Base → KALAH",                        (255,100,100), False),
        ("",                                                     None,           False),
        ("LEVEL:",                                               (180, 220, 255), False),
        ("  Level 1: rawa di dekat Base (kanan)",                 C_TEXT,        False),
        ("  Level 2: rawa di dekat Base DAN Spawn + rintangan bawaan",
                                                                  C_TEXT,        False),
        ("",                                                     None,           False),
        ("KONTROL:",                                             (180, 220, 255), False),
        ("  Drag klik kiri = bangun obstacle",                    C_TEXT,        False),
        ("  R             = Restart level",                       C_TEXT,        False),
        ("  ESC           = Kembali ke menu",                     C_TEXT,        False),
    ]

    def __init__(self, screen):
        self.screen   = screen
        self.font     = pygame.font.SysFont("consolas", 14)
        self.font_b   = pygame.font.SysFont("consolas", 14, bold=True)
        self.font_btn = pygame.font.SysFont("consolas", 18, bold=True)
        self.btn_back = Button(
            (SCREEN_W // 2 - 110, SCREEN_H - 52, 220, 42),
            "Kembali ke Menu", self.font_btn,
        )

    def handle_event(self, event):
        """Kembalikan True jika tombol Kembali diklik atau ESC ditekan."""
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return True
        return self.btn_back.handle_event(event)

    def draw(self):
        self.screen.fill(C_BG)
        y = 25
        for text, color, bold in self.LINES:
            if not text:
                y += 7
                continue
            font = self.font_b if bold else self.font
            lbl  = font.render(text, True, color or C_TEXT)
            self.screen.blit(lbl, (45, y))
            y += 21
        self.btn_back.draw(self.screen)


# ─────────────────────────────────────────────
#  LEVEL TRANSITION SCREEN
# ─────────────────────────────────────────────
class LevelTransition:
    """Layar transisi saat Level N selesai → Level N+1."""

    def __init__(self, screen, from_level, to_level):
        self.screen     = screen
        self.from_level = from_level
        self.to_level   = to_level
        self.font_big   = pygame.font.SysFont("consolas", 52, bold=True)
        self.font_mid   = pygame.font.SysFont("consolas", 20)
        self.font_btn   = pygame.font.SysFont("consolas", 20, bold=True)
        self.btn_next   = Button(
            (SCREEN_W // 2 - 150, 390, 300, 55),
            f"Lanjut ke Level {to_level}",
            self.font_btn,
        )

    def handle_event(self, event):
        """Kembalikan True jika tombol diklik ATAU Enter/Space ditekan."""
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE):
            return True
        return self.btn_next.handle_event(event)

    def draw(self):
        self.screen.fill(C_BG)

        # Overlay hijau samar
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 30, 10, 55))
        self.screen.blit(overlay, (0, 0))

        cx = SCREEN_W // 2

        title = self.font_big.render(f"Level {self.from_level} Clear!", True, (50, 220, 100))
        self.screen.blit(title, (cx - title.get_width() // 2, 175))

        sub = self.font_mid.render("BFS: Semua jalur berhasil diblokir!", True, (180, 255, 180))
        self.screen.blit(sub, (cx - sub.get_width() // 2, 270))

        hint = self.font_mid.render(
            f"Level {self.to_level}: area No-Build makin luas — strategi baru diperlukan!",
            True, (210, 210, 150),
        )
        self.screen.blit(hint, (cx - hint.get_width() // 2, 310))

        hint2 = self.font_mid.render(
            "Tekan ENTER / SPACE atau klik tombol di bawah", True, (160, 160, 170)
        )
        self.screen.blit(hint2, (cx - hint2.get_width() // 2, 348))

        self.btn_next.draw(self.screen)
