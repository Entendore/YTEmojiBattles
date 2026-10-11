#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧬 Emoji Evolution Battle Arena ⚔️ — v5.1 NEURAL WARFARE EDITION

UNITS (32):  ⚔️🛡️🪓🐎🐺🦁🐗🧟💀🧛🐻🦀👹🦖🦂🕷️🐝🏹🧝🧙👽🤖🐉🦅🦇🦉👻🔥🎃🧚👼🦄
TERRAIN(13): 🌱🏜️🌊🌲🪨🌺🧊🌋🌵🍄🍃⛲🧱 — slow/armor/heal/DoT/slippery/impassable
BIOMES(6):   🌿 Plains · 🌲 Forest · 🏜️ Desert · 🌋 Volcanic · 🧊 Arctic · 🥦 Swamp
PRESETS(9):  ⚔️ Classic · 🌲 Forest Battle · 🏜️ Desert Canyon · 🌋 Volcanic Rift
             🧊 Frozen Lake · 🥦 Murky Swamp · 🎯 Open Field · 🎲 Chaos Realm · 🏝️ Island
PICKUPS:     🧪 potion · 💰 fitness gold · ⚡ speed · 🛡️ shield  (toggleable!)
COMBAT:      ✨ crits · 🩸 lifesteal · ☠️ poison · 🛡️ armor · 💥 kamikaze pumpkins
             · 🌅 phoenix rebirth · lunge/hit-flash · ⚡🔥💀 kill streaks · 💥 KNOCKBACK
BRAIN:       31→24→10 neural net per unit — click a unit for a 🧠 live brain viewer
             Outputs: ➡️ X  ⬆️ Y  ⚔️ Act  🎯 Tgt  🏃 Flee  🎁 Loot
                      🧭 Roam  🛡️ Defend  🤝 Formation  🏹 Kite
EVOLUTION:   per (team,type) gene pools · 👑 elites · 🏆 hall-of-fame · tournament
             selection · crossover · mutation · 📈 fitness graph · 💾/📂 save-load
             · Stagnation injection · Blitzkrieg fitness · Sudden death
FORMATION:   🎲 📏 🛡️ 🔺 🎯 spawn layouts (wall auto-places ranged behind melee)
YOUTUBE SHORTS: 📦 Batch export multiple MP4s automatically · 1080×1920 9:16 format
PERF:        🧮 NumPy batched brains (pure-Python fallback) · 🗺️ spatial hash grid
             · 📡 flat-array sensing · 🖼️ sprite caches (bg + fg split)
             · 🧱 tile-change-only terrain · 💥 particle caps · 🏁 O(1) win checks
             · 🪶 light-FX · 🎛️ throttled turbo · live 🖥️ FPS / ⚙️ steps-per-sec meters
             · 🧠 NN & 🧬 GA execution timing · ⏱️ Hard 180s battle cap
HOTKEYS:     ⌨️ Space = start/pause · N = next battle

Requires:  pip install PySide6            (optional: pip install numpy opencv-python)
Run:       python app.py
"""

import json
import math
import os
import random
import sys
import time
from dataclasses import dataclass
from typing import Optional, Any

try:
    import numpy as _np
except Exception:
    _np = None

try:
    import cv2
    HAS_CV2 = True
except Exception:
    HAS_CV2 = False

from PySide6.QtCore import Qt, QTimer, QPointF, QRectF
from PySide6.QtGui import (QColor, QFont, QFontDatabase, QImage, QKeySequence, QPainter,
                           QPen, QPixmap, QPolygonF, QShortcut, QRadialGradient)
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDoubleSpinBox, QFileDialog,
    QGridLayout, QGroupBox, QHBoxLayout, QLabel, QMainWindow,
    QPlainTextEdit, QProgressBar, QPushButton, QScrollArea, QSlider,
    QSpinBox, QVBoxLayout, QWidget, QSizePolicy,
)

APP_TITLE = "🧬 Emoji Evolution Battle Arena ⚔️ v5.1 — Neural Warfare Edition"

COLS, ROWS = 28, 17
N_IN, N_HID, N_OUT = 31, 24, 10  # Upgraded: N_IN 28 -> 31 for Hazard Sensing
GENOME_LEN = N_IN * N_HID + N_HID + N_HID * N_OUT + N_OUT
K1 = N_IN * N_HID
K2 = K1 + N_HID
K3 = K2 + N_HID * N_OUT

TEAM_HEX    = ("#3d8bfd", "#ff5c5c")
TEAM_COLORS = (QColor("#3d8bfd"), QColor("#ff5c5c"))

FORM_KEYS   = ["random", "line", "wall", "wedge", "spread"]
FORM_LABELS = ["🎲 Random", "📏 Line", "🛡️ Wall", "🔺 Wedge", "🎯 Spread"]
PICKUP_KINDS = ("🧪", "💰", "⚡", "🛡️")

MAX_PARTS = 320
GRID_CS   = 4.0
MAX_BATTLE_TIME = 180.0  # 3 minutes hard cap

# ----------------------------- Biomes & Presets -----------------------------
BIOMES: dict[str, dict[str, Any]] = {
    "plains": {
        "name": "🌿 Plains",
        "base": "grass",
        "features": [
            ("flowers", 3, 6), ("fountain", 3, 2), ("forest", 2, 8),
            ("rock", 2, 6), ("water", 1, 8), ("sand", 1, 6),
        ],
    },
    "forest": {
        "name": "🌲 Deep Forest",
        "base": "grass",
        "features": [
            ("forest", 6, 18), ("mushroom", 4, 6), ("swamp", 2, 8),
            ("rock", 2, 5), ("fountain", 2, 2), ("flowers", 2, 5),
        ],
    },
    "desert": {
        "name": "🏜️ Desert",
        "base": "sand",
        "features": [
            ("cactus", 5, 8), ("rock", 4, 10), ("water", 1, 6),
            ("flowers", 1, 4), ("sand", 3, 12), ("rock", 2, 6),
        ],
    },
    "volcanic": {
        "name": "🌋 Volcanic",
        "base": "rock",
        "features": [
            ("lava", 4, 12), ("rock", 5, 12), ("swamp", 2, 6),
            ("wall", 2, 8), ("cactus", 2, 4), ("lava", 2, 6),
        ],
    },
    "arctic": {
        "name": "🧊 Arctic",
        "base": "ice",
        "features": [
            ("ice", 5, 14), ("water", 3, 10), ("rock", 3, 8),
            ("forest", 1, 6), ("ice", 3, 8), ("flowers", 1, 3),
        ],
    },
    "swamp": {
        "name": "🥦 Swamp",
        "base": "swamp",
        "features": [
            ("swamp", 5, 14), ("water", 3, 10), ("mushroom", 4, 6),
            ("forest", 2, 8), ("rock", 1, 4), ("flowers", 1, 3),
        ],
    },
}

LEVEL_PRESETS: dict[str, dict[str, Any]] = {
    "classic":       {"name": "⚔️ Classic Arena",   "biome": "plains",   "features_scale": 1.0,  "paths": 3},
    "forest_battle": {"name": "🌲 Forest Battle",    "biome": "forest",   "features_scale": 1.2,  "paths": 2},
    "desert_canyon": {"name": "🏜️ Desert Canyon",    "biome": "desert",   "features_scale": 1.0,  "paths": 3},
    "volcanic_rift": {"name": "🌋 Volcanic Rift",    "biome": "volcanic", "features_scale": 1.3,  "paths": 2},
    "frozen_lake":   {"name": "🧊 Frozen Lake",      "biome": "arctic",   "features_scale": 1.1,  "paths": 3},
    "murky_swamp":   {"name": "🥦 Murky Swamp",       "biome": "swamp",    "features_scale": 1.0,  "paths": 2},
    "open_field":    {"name": "🎯 Open Field",       "biome": "plains",   "features_scale": 0.3,  "paths": 4},
    "chaos_realm":   {"name": "🎲 Chaos Realm",      "biome": "volcanic", "features_scale": 1.6,  "paths": 1},
    "island":        {"name": "🏝️ Island",           "biome": "plains",   "features_scale": 0.7,  "paths": 2, "extra_water": True},
}

def clamp(v: float, lo: float, hi: float) -> float:
    return lo if v < lo else (hi if v > hi else v)

# ----------------------------- Data Models -----------------------------
@dataclass(frozen=True)
class TerrainType:
    base: str
    feat: Optional[str]
    speed: float
    df: float
    heal: float
    dot: float
    slip: bool
    pas: bool

TERRAIN: dict[str, TerrainType] = {
    "grass":    TerrainType("🌱", None,  1.00, 1.00, 0.0, 0.0, False, True),
    "sand":     TerrainType("🏜️", None,  1.18, 0.90, 0.0, 0.0, False, True),
    "water":    TerrainType("🌊", None,  0.00, 1.00, 0.0, 0.0, False, False),
    "forest":   TerrainType("🌲", None,  0.62, 1.38, 0.0, 0.0, False, True),
    "rock":     TerrainType("🪨", None,  0.00, 1.00, 0.0, 0.0, False, False),
    "flowers":  TerrainType("🌺", None,  1.00, 1.05, 3.0, 0.0, False, True),
    "ice":      TerrainType("🧊", None,  1.05, 0.95, 0.0, 0.0, True,  True),
    "lava":     TerrainType("🌋", None,  0.60, 1.00, 0.0, 9.0, False, True),
    "cactus":   TerrainType("🌵", None,  0.80, 1.00, 0.0, 4.0, False, True),
    "mushroom": TerrainType("🍄", None,  0.90, 1.00, 0.0, 3.0, False, True),
    "swamp":    TerrainType("🍃", None,  0.55, 1.05, 0.0, 1.5, False, True),
    "fountain": TerrainType("⛲", None,  1.00, 1.00, 8.0, 0.0, False, True),
    "wall":     TerrainType("🧱", None,  0.00, 1.00, 0.0, 0.0, False, False),
}

@dataclass(frozen=True)
class UnitType:
    key: str
    emoji: str
    name: str
    hp: int
    atk: int
    rng: float
    speed: float
    cd: float
    ranged: bool = False
    armor: float = 1.0
    crit: float = 0.12
    lifesteal: float = 0.0
    fly: bool = False
    phase: bool = False
    poison: Optional[tuple[float, float]] = None
    heal_power: Optional[int] = None
    revive: bool = False
    lava_immune: bool = False
    explode: Optional[tuple[int, float]] = None
    proj_speed: float = 0.0
    proj_emoji: Optional[str] = None
    splash: bool = False
    hid: int = 24

def U(key: str, emoji: str, name: str, hp: int, atk: int, rng: float, speed: float, cd: float, **kw: Any) -> UnitType:
    return UnitType(key, emoji, name, hp, atk, rng, speed, cd, **kw)

HID_SMALL, HID_MED, HID_LARGE = 16, 24, 32

UNIT_TYPES: list[UnitType] = [
    U("warrior",  "⚔️", "Warrior",   135, 16, 1.5, 1.70, 0.70, hid=HID_MED),
    U("guardian", "🛡️", "Guardian",  230, 11, 1.5, 1.30, 0.90, armor=0.75, hid=HID_MED),
    U("berserker","🪓", "Berserker", 100, 22, 1.4, 1.90, 0.85, crit=0.22, hid=HID_MED),
    U("cavalry",  "🐎", "Cavalry",   115, 14, 1.5, 2.50, 0.80, hid=HID_MED),
    U("wolf",     "🐺", "Wolf",       90, 13, 1.3, 2.30, 0.60, hid=HID_SMALL),
    U("lion",     "🦁", "Lion",      140, 19, 1.5, 1.95, 0.90, crit=0.18, hid=HID_MED),
    U("boar",     "🐗", "Boar",      175, 13, 1.4, 1.80, 0.95, hid=HID_SMALL),
    U("zombie",   "🧟", "Zombie",    150, 12, 1.3, 0.95, 1.00, hid=HID_SMALL),
    U("skeleton", "💀", "Skeleton",   70, 10, 1.3, 1.55, 0.70, hid=HID_SMALL),
    U("vampire",  "🧛", "Vampire",   120, 15, 1.5, 1.75, 0.80, lifesteal=0.6, hid=HID_MED),
    U("bear",     "🐻", "Bear",      210, 20, 1.5, 1.35, 1.05, hid=HID_MED),
    U("crab",     "🦀", "Crab",      160,  9, 1.4, 0.90, 0.95, armor=0.50, hid=HID_SMALL),
    U("ogre",     "👹", "Ogre",      260, 26, 1.6, 1.00, 1.35, armor=0.85, hid=HID_LARGE),
    U("trex",     "🦖", "T-Rex",     420, 45, 1.9, 1.05, 1.60, armor=0.85, crit=0.15, hid=HID_LARGE),
    U("scorpion", "🦂", "Scorpion",  105, 11, 1.4, 1.35, 0.95, poison=(5.0, 3.5), armor=0.85, hid=HID_SMALL),
    U("spider",   "🕷️", "Spider",     95, 10, 1.4, 1.60, 0.90, poison=(4.0, 3.0), hid=HID_SMALL),
    U("wasp",     "🐝", "Wasp",       55,  7, 1.2, 2.60, 0.42, poison=(2.5, 2.5), hid=HID_SMALL),
    U("archer",   "🏹", "Archer",     85, 14, 5.2, 1.50, 1.05, ranged=True, proj_speed=9.5, hid=HID_MED),
    U("elf",      "🧝", "Elf",        80, 11, 7.0, 1.70, 0.95, ranged=True, proj_speed=12.0, hid=HID_MED),
    U("mage",     "🧙", "Mage",       70, 28, 4.2, 1.15, 1.70, ranged=True, proj_speed=6.0, proj_emoji="✨", splash=True, hid=HID_LARGE),
    U("alien",    "👽", "Alien",      95, 18, 4.4, 1.60, 1.20, ranged=True, proj_speed=8.0, proj_emoji="☄️", hid=HID_LARGE),
    U("robot",    "🤖", "Robot",     170, 15, 4.8, 1.05, 0.85, ranged=True, proj_speed=14.0, proj_emoji="⚡", armor=0.80, hid=HID_LARGE),
    U("dragon",   "🐉", "Dragon",    190, 24, 3.6, 1.40, 1.40, ranged=True, proj_speed=7.0, proj_emoji="🔥", fly=True, hid=HID_LARGE),
    U("griffin",  "🦅", "Griffin",   130, 18, 1.6, 2.35, 0.85, fly=True, hid=HID_MED),
    U("bat",      "🦇", "Bat",        45,  7, 1.2, 2.75, 0.50, fly=True, hid=HID_SMALL),
    U("owl",      "🦉", "Owl",        70,  9, 2.0, 2.45, 0.75, fly=True, hid=HID_SMALL),
    U("ghost",    "👻", "Ghost",     110, 14, 1.5, 1.10, 1.00, phase=True, armor=0.85, hid=HID_MED),
    U("phoenix",  "🔥", "Phoenix",   150, 20, 1.7, 1.55, 1.05, fly=True, revive=True, lava_immune=True, hid=HID_LARGE),
    U("pumpkin",  "🎃", "Pumpkin",    80,  6, 1.3, 1.25, 1.10, explode=(42, 2.3), hid=HID_SMALL),
    U("fairy",    "🧚", "Fairy",      80,  0, 3.6, 1.45, 1.00, heal_power=16, hid=HID_MED),
    U("angel",    "👼", "Angel",      95,  0, 4.0, 1.35, 1.05, fly=True, heal_power=14, hid=HID_MED),
    U("unicorn",  "🦄", "Unicorn",   125, 14, 1.6, 1.75, 0.95, heal_power=10, hid=HID_MED),
]
TYPE_BY_KEY: dict[str, UnitType] = {t.key: t for t in UNIT_TYPES}

# ----------------------------- Fonts & Caching -----------------------------
_EMOJI_FAMILIES = ["Apple Color Emoji", "Segoe UI Emoji", "Noto Color Emoji",
                   "EmojiOne Color", "Twemoji Mozilla", "Noto Emoji"]
_BEST_EMOJI_FAMILY = None
_font_cache: dict[Any, QFont] = {}
_pm_cache: dict[tuple[str, int], QPixmap] = {}

def _init_emoji_font_family() -> None:
    global _BEST_EMOJI_FAMILY
    if _BEST_EMOJI_FAMILY is not None:
        return
    try:
        families = QFontDatabase.families()
        for cand in _EMOJI_FAMILIES:
            if any(cand.lower() == f.lower() for f in families):
                _BEST_EMOJI_FAMILY = cand
                print(f"✅ Using emoji font: '{_BEST_EMOJI_FAMILY}'")
                return
        for f in families:
            if 'emoji' in f.lower():
                _BEST_EMOJI_FAMILY = f
                print(f"✅ Fallback to emoji font: '{_BEST_EMOJI_FAMILY}'")
                return
        print("⚠️ WARNING: No emoji font detected. Falling back to system default.")
        _BEST_EMOJI_FAMILY = ""
    except Exception as e:
        print(f"⚠️ Font detection error: {e}")
        _BEST_EMOJI_FAMILY = ""

def emoji_font(px: int) -> QFont:
    _init_emoji_font_family()
    f = _font_cache.get(px)
    if f is None:
        f = QFont()
        if _BEST_EMOJI_FAMILY:
            f.setFamily(_BEST_EMOJI_FAMILY)
        f.setPixelSize(max(8, px))
        f.setStyleStrategy(QFont.StyleStrategy.PreferMatch)
        f.setHintingPreference(QFont.HintingPreference.PreferNoHinting)
        _font_cache[px] = f
    return f

def text_font(px: int) -> QFont:
    key = ("t", px)
    f = _font_cache.get(key)
    if f is None:
        f = QFont()
        f.setPixelSize(px)
        f.setBold(True)
        _font_cache[key] = f
    return f

def emoji_pm(ch: str, px: int) -> QPixmap:
    pm = _pm_cache.get((ch, px))
    if pm is None:
        pm = QPixmap(px, px)
        pm.fill(QColor(0, 0, 0, 0))
        pp = QPainter(pm)
        pp.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        pp.setPen(QColor(255, 255, 255))
        pp.setFont(emoji_font(px))
        pp.drawText(QRectF(0, 0, px, px), Qt.AlignmentFlag.AlignCenter, ch)
        pp.end()
        _pm_cache[(ch, px)] = pm
    return pm

# ----------------------------- Spatial Hash Grid -----------------------------
class SGrid:
    __slots__ = ("cs", "cols", "rows", "cells")

    def __init__(self) -> None:
        self.cs = GRID_CS
        self.cols = int(math.ceil(COLS / GRID_CS))
        self.rows = int(math.ceil(ROWS / GRID_CS))
        self.cells: dict[tuple[int, int], list["Unit"]] = {}

    def build(self, units: list["Unit"]) -> None:
        cells: dict[tuple[int, int], list["Unit"]] = {}
        cs = self.cs
        for u in units:
            k = (int(u.x / cs), int(u.y / cs))
            c = cells.get(k)
            if c is None: cells[k] = [u]
            else: c.append(u)
        self.cells = cells

    def nearby(self, x: float, y: float, r: float) -> list["Unit"]:
        cs = self.cs
        x0 = max(0, int((x - r) / cs)); x1 = min(self.cols - 1, int((x + r) / cs))
        y0 = max(0, int((y - r) / cs)); y1 = min(self.rows - 1, int((y + r) / cs))
        cells = self.cells
        out: list["Unit"] = []
        for cx in range(x0, x1 + 1):
            for cy in range(y0, y1 + 1):
                c = cells.get((cx, cy))
                if c: out.extend(c)
        return out

# ----------------------------- Neural Network -----------------------------
def _genome_layout(hid: int) -> tuple[int, int, int, int, int]:
    k1 = N_IN * hid
    k2 = k1 + hid
    k3 = k2 + hid * N_OUT
    return k1, k2, k3, k3 + N_OUT, hid

K1, K2, K3, GENOME_LEN, _ = _genome_layout(N_HID)

def genome_len_for_type(key: str) -> int:
    t = TYPE_BY_KEY.get(key)
    if t is None:
        return GENOME_LEN
    return _genome_layout(t.hid)[3]

def random_genome_for_type(key: str) -> list[float]:
    return [random.uniform(-1, 1) for _ in range(genome_len_for_type(key))]

def random_genome() -> list[float]:
    return [random.uniform(-1, 1) for _ in range(GENOME_LEN)]


class NN:
    __slots__ = ("ni", "nh", "no", "w", "k1", "k2", "k3", "glen", "W1", "b1", "W2", "b2")

    def __init__(self, ni: int, nh: int, no: int, genome: Optional[list[float]] = None) -> None:
        self.ni, self.nh, self.no = ni, nh, no
        self.k1, self.k2, self.k3, self.glen, _ = _genome_layout(nh)
        if genome is None:
            genome = [random.uniform(-1, 1) for _ in range(self.glen)]
        self.w = list(genome)
        if _np is not None:
            self.W1 = _np.array(self.w[:self.k1]).reshape(nh, ni)
            self.b1 = _np.array(self.w[self.k1:self.k2])
            self.W2 = _np.array(self.w[self.k2:self.k3]).reshape(no, nh)
            self.b2 = _np.array(self.w[self.k3:])
        else:
            self.W1 = self.b1 = self.W2 = self.b2 = None

    def forward(self, inp: list[float]) -> tuple[list[float], list[float]]:
        w = self.w; ni, nh, no = self.ni, self.nh, self.no
        k = 0
        hid = [0.0] * nh
        for h in range(nh):
            s = 0.0
            for i in range(ni):
                s += inp[i] * w[k]; k += 1
            hid[h] = math.tanh(s + w[k]); k += 1
        out = [0.0] * no
        for o in range(no):
            s = 0.0
            for h in range(nh):
                s += hid[h] * w[k]; k += 1
            out[o] = s + w[k]; k += 1
        return out, hid

def forward_batch(batch: list[tuple["NN", list[float]]]) -> tuple[list[list[float]], list[list[float]]]:
    if not batch:
        return [], []
    if _np is not None:
        groups: dict[int, list[int]] = {}
        for i, (nn, _inp) in enumerate(batch):
            groups.setdefault(nn.nh, []).append(i)

        outs: list[Optional[list[float]]] = [None] * len(batch)
        hids: list[Optional[list[float]]] = [None] * len(batch)
        for nh, idxs in groups.items():
            if len(idxs) > 1:
                X  = _np.array([batch[i][1] for i in idxs])
                W1 = _np.stack([batch[i][0].W1 for i in idxs])
                b1 = _np.stack([batch[i][0].b1 for i in idxs])
                H  = _np.einsum('bi,bhi->bh', X, W1) + b1
                _np.tanh(H, out=H)
                W2 = _np.stack([batch[i][0].W2 for i in idxs])
                b2 = _np.stack([batch[i][0].b2 for i in idxs])
                O  = _np.einsum('bh,boh->bo', H, W2) + b2
                o_list, h_list = O.tolist(), H.tolist()
                for j, idx in enumerate(idxs):
                    outs[idx] = o_list[j]; hids[idx] = h_list[j]
            else:
                idx = idxs[0]
                nn, inp = batch[idx]
                o, h = nn.forward(inp)
                outs[idx] = o; hids[idx] = h
        return outs, hids  # type: ignore
    outs: list[list[float]] = []
    hids: list[list[float]] = []
    for nn, inp in batch:
        o, h = nn.forward(inp)
        outs.append(o); hids.append(h)
    return outs, hids

# ----------------------------- Entities -----------------------------
class Unit:
    __slots__ = ("battle", "team", "t", "x", "y", "hp", "max_hp", "cd",
                 "genome", "nn", "think_t", "mvx", "mvy", "gate", "target",
                 "alive", "fit_dmg", "fit_kills", "fit_time", "fit_heal", "fit_gold",
                 "tsp", "tdf", "theal", "tdot", "tslip", "tname",
                 "slipx", "slipy", "flash", "lunge_t", "lx", "ly",
                 "poison_t", "poison_dps", "poison_src",
                 "fly", "phase", "elite", "streak",
                 "buff_spd_t", "buff_shd_t", "used_revive",
                 "a_in", "a_hid", "a_out", "_ai",
                 "_e1i", "_low_hp_ei", "target_mode", "flee_mode", "pickup_mode",
                 "roam_mode", "defensive_mode", "formation_mode", "kite_mode",
                 "disp_hp", "fade_t")

    def __init__(self, battle: "Battle", team: int, tkey: str, x: float, y: float, genome: list[float], elite: bool = False) -> None:
        self.battle = battle
        self.team = team
        self.t = TYPE_BY_KEY[tkey]
        self.x, self.y = x, y
        self.max_hp = self.t.hp
        self.hp = self.max_hp
        self.disp_hp = float(self.max_hp)
        self.cd = 0.0
        self.genome = genome
        self.nn = NN(N_IN, self.t.hid, N_OUT, genome)
        self.think_t = random.random() * 0.1
        self.mvx = self.mvy = self.gate = 0.0
        self.target: Optional["Unit"] = None
        self.alive = True
        self.fade_t = 0.0
        self.fit_dmg = 0.0
        self.fit_kills = 0
        self.fit_time = 0.0
        self.fit_heal = 0.0
        self.fit_gold = 0.0
        self.tsp, self.tdf, self.theal, self.tdot, self.tslip = 1.0, 1.0, 0.0, 0.0, False
        self.tname: Optional[str] = None
        self.slipx = self.slipy = 0.0
        self.flash = 0.0
        self.lunge_t = 0.0
        self.lx = self.ly = 0.0
        self.poison_t = 0.0
        self.poison_dps = 0.0
        self.poison_src: Optional["Unit"] = None
        self.fly = self.t.fly
        self.phase = self.t.phase
        self.elite = elite
        self.streak = 0
        self.buff_spd_t = 0.0
        self.buff_shd_t = 0.0
        self.used_revive = False
        self.a_in = None
        self.a_hid = None
        self.a_out = None
        self._ai = 0
        self._e1i = -1
        self._low_hp_ei = -1
        self.target_mode = 0.0
        self.flee_mode = 0.0
        self.pickup_mode = 0.0
        self.roam_mode = 0.0
        self.defensive_mode = 0.0
        self.formation_mode = 0.0
        self.kite_mode = 0.0
        battle.update_tile(self)

    def sense(self) -> list[float]:
        b = self.battle
        au = b._au; ax = b._ax; ay = b._ay; at = b._ateam
        ah = b._ahp; am = b._ahpm
        n = len(au); i = self._ai
        x = ax[i]; y = ay[i]; team = self.team
        e1i = e2i = a1i = w1i = low_hp_ei = -1
        e1d = e2d = ad = wd = low_hp_d = 1e18
        low_hp_ratio = 2.0
        ne = na = 0; sr2 = b._sr2

        for j in range(n):
            if j == i: continue
            dx = ax[j] - x; dy = ay[j] - y
            d2 = dx * dx + dy * dy
            if at[j] == team:
                if d2 < ad: ad = d2; a1i = j
                if d2 < wd and ah[j] < am[j] * 0.92: wd = d2; w1i = j
                if d2 <= sr2: na += 1
            else:
                if d2 < e1d: e2d = e1d; e2i = e1i; e1d = d2; e1i = j
                elif d2 < e2d: e2d = d2; e2i = j
                hp_ratio = ah[j] / am[j]
                if hp_ratio < low_hp_ratio:
                    low_hp_ratio = hp_ratio
                    low_hp_ei = j
                if d2 <= sr2: ne += 1

        inp = [0.0] * N_IN
        inp[0] = self.hp / self.max_hp
        rng = self.t.rng
        sdiv = b._sdiv; ddiv = b._ddiv

        if e1i >= 0:
            d = math.sqrt(e1d)
            inp[1] = clamp((ax[e1i] - x) / sdiv, -1, 1)
            inp[2] = clamp((ay[e1i] - y) / sdiv, -1, 1)
            inp[3] = d / ddiv if d < ddiv else 1.0
            inp[4] = ah[e1i] / am[e1i]
            self.target = au[e1i]
            inp[15] = 1.0 if d <= rng + 0.2 else 0.0
            inp[23] = au[e1i].mvx
            inp[24] = au[e1i].mvy
            if e2i >= 0:
                d = math.sqrt(e2d)
                inp[5] = clamp((ax[e2i] - x) / sdiv, -1, 1)
                inp[6] = clamp((ay[e2i] - y) / sdiv, -1, 1)
                inp[7] = d / ddiv if d < ddiv else 1.0
        else:
            self.target = None
            inp[23] = 0.0
            inp[24] = 0.0

        if a1i >= 0:
            inp[8]  = clamp((ax[a1i] - x) / sdiv, -1, 1)
            inp[9]  = clamp((ay[a1i] - y) / sdiv, -1, 1)
            inp[10] = ah[a1i] / am[a1i]

        if w1i >= 0:
            inp[18] = clamp((ax[w1i] - x) / sdiv, -1, 1)
            inp[19] = clamp((ay[w1i] - y) / sdiv, -1, 1)

        inp[11] = ne * 0.2 if ne < 5 else 1.0
        inp[12] = na * 0.2 if na < 5 else 1.0
        inp[13] = self.tsp
        inp[14] = (self.tdf - 1.0) * 2.5
        inp[16] = 1.0 if self.cd <= 0.0 else 0.0
        inp[17] = clamp((self.battle.limit - self.battle.time) / 180.0, 0.0, 1.0)

        if b.pickups:
            p1 = None; pd = 1e18
            for pk in b.pickups:
                d2 = (pk[1] - x) ** 2 + (pk[2] - y) ** 2
                if d2 < pd: pd = d2; p1 = pk
            if p1:
                inp[20] = clamp((p1[1] - x) / 6, -1, 1)
                inp[21] = clamp((p1[2] - y) / 6, -1, 1)
                inp[22] = 1.0

        ally_hp_sum = 0.0; ally_max_sum = 0.0
        enemy_hp_sum = 0.0; enemy_max_sum = 0.0
        ally_cnt = 0; enemy_cnt = 0
        for j in range(n):
            if at[j] == team:
                ally_hp_sum += ah[j]; ally_max_sum += am[j]; ally_cnt += 1
            else:
                enemy_hp_sum += ah[j]; enemy_max_sum += am[j]; enemy_cnt += 1
        inp[25] = ally_hp_sum / ally_max_sum if ally_max_sum > 0 else 0.0
        inp[26] = enemy_hp_sum / enemy_max_sum if enemy_max_sum > 0 else 0.0
        
        ally_focus = 0
        if e1i >= 0:
            for j in range(n):
                if at[j] == team and au[j].target is not None and au[j].target._ai == e1i:
                    ally_focus += 1
        inp[27] = clamp(ally_focus / 4.0, 0.0, 1.0)

        # NEW: Terrain Hazard Sensing
        if not self.fly and not self.phase:
            ix, iy = int(self.x), int(self.y)
            best_hzd = 5.0
            hzx, hzy = 0.0, 0.0
            for ddx in range(-3, 4):
                for ddy in range(-3, 4):
                    if ddx == 0 and ddy == 0: continue
                    nx = clamp(ix + ddx, 0, COLS - 1)
                    ny = clamp(iy + ddy, 0, ROWS - 1)
                    tt = TERRAIN[b.terrain[nx][ny]]
                    if not tt.pas or (tt.dot > 0 and not self.t.lava_immune):
                        dx = (nx + 0.5) - self.x
                        dy = (ny + 0.5) - self.y
                        dist = math.hypot(dx, dy)
                        if dist < best_hzd:
                            best_hzd = dist
                            hzx, hzy = dx, dy
            if best_hzd < 5.0:
                inp[28] = clamp(hzx / 4.0, -1, 1)
                inp[29] = clamp(hzy / 4.0, -1, 1)
                inp[30] = best_hzd / 4.0
        else:
            inp[28] = 0.0
            inp[29] = 0.0
            inp[30] = 1.0 # max distance / safe

        self._e1i = e1i
        self._low_hp_ei = low_hp_ei
        return inp

    def set_action(self, inp: list[float], out: list[float], hid: list[float]) -> None:
        self.a_in = inp
        self.a_hid = hid
        self.a_out = out

        self.mvx = math.tanh(out[0])
        self.mvy = math.tanh(out[1])
        l = self.mvx * self.mvx + self.mvy * self.mvy
        if l > 1.0:
            l = math.sqrt(l); self.mvx /= l; self.mvy /= l

        self.gate = 1.0 / (1.0 + math.exp(-out[2]))
        self.target_mode = 1.0 / (1.0 + math.exp(-out[3]))
        self.flee_mode = 1.0 / (1.0 + math.exp(-out[4]))
        self.pickup_mode = 1.0 / (1.0 + math.exp(-out[5]))
        self.roam_mode = 1.0 / (1.0 + math.exp(-out[6]))
        self.defensive_mode = 1.0 / (1.0 + math.exp(-out[7]))
        self.formation_mode = 1.0 / (1.0 + math.exp(-out[8]))
        self.kite_mode = 1.0 / (1.0 + math.exp(-out[9]))

        if self._low_hp_ei >= 0 and self.target_mode > 0.5:
            self.target = self.battle._au[self._low_hp_ei]
        elif self._e1i >= 0:
            self.target = self.battle._au[self._e1i]
        else:
            self.target = None


class Proj:
    __slots__ = ("x", "y", "vx", "vy", "team", "dmg", "ttl", "src", "emoji", "splash", "crit")

    def __init__(self, src: Unit, tx: float, ty: float) -> None:
        self.src = src
        self.team = src.team
        self.dmg = src.t.atk
        self.x, self.y = src.x, src.y
        d = math.hypot(tx - src.x, ty - src.y) or 1e-6
        ps = src.t.proj_speed
        self.vx = (tx - src.x) / d * ps
        self.vy = (ty - src.y) / d * ps
        self.ttl = d / ps + 0.35
        self.emoji = src.t.proj_emoji
        self.splash = src.t.splash
        self.crit = False

# ----------------------------- Shorts Exporter -----------------------------
class ShortsExporter:
    def __init__(self) -> None:
        self.recording = False
        self.writer = None
        self.path = ""
        self.fps = 30
        self.width = 1080
        self.height = 1920
        self.frame_count = 0
        self.max_frames = 30 * 60
        self.last_capture = 0.0
        self.capture_interval = 1.0 / 30.0

    def start(self, path: str) -> bool:
        if not HAS_CV2:
            return False
        self.path = path
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.writer = cv2.VideoWriter(path, fourcc, self.fps, (self.width, self.height))
        if not self.writer.isOpened():
            return False
        self.recording = True
        self.frame_count = 0
        self.last_capture = 0.0
        return True

    def capture(self, widget: QWidget) -> None:
        if not self.recording or self.writer is None:
            return
        if self.frame_count >= self.max_frames:
            return

        now = time.perf_counter()
        if now - self.last_capture < self.capture_interval:
            return
        self.last_capture = now

        pm = widget.grab()
        w, h = pm.width(), pm.height()

        target_ratio = 9.0 / 16.0
        current_ratio = w / h

        if current_ratio > target_ratio:
            crop_h = h
            crop_w = int(h * target_ratio)
        else:
            crop_w = w
            crop_h = int(w / target_ratio)

        x = (w - crop_w) // 2
        y = (h - crop_h) // 2

        pm = pm.copy(x, y, crop_w, crop_h)

        img = pm.toImage().scaled(self.width, self.height,
                                  Qt.AspectRatioMode.IgnoreAspectRatio,
                                  Qt.TransformationMode.SmoothTransformation)
        img = img.convertToFormat(QImage.Format_RGBA8888)

        if _np is not None:
            ptr = img.constBits()
            ptr.setsize(img.sizeInBytes())
            arr = _np.frombuffer(ptr, dtype=_np.uint8).reshape(self.height, self.width, 4)
            arr_bgr = cv2.cvtColor(arr, cv2.COLOR_RGBA2BGR)
            self.writer.write(arr_bgr)

        self.frame_count += 1

    def stop(self) -> tuple[str, int]:
        self.recording = False
        if self.writer:
            self.writer.release()
            self.writer = None
        return self.path, self.frame_count

# ----------------------------- Battle System -----------------------------
class Battle:
    def __init__(self, counts: dict[tuple[int, str], int], limit: int, breeder: "Breeder",
                 new_map: bool, formation: str = "random", pickups: bool = True) -> None:
        self.counts = counts
        self.limit = min(float(limit), MAX_BATTLE_TIME)
        self.formation = formation
        self.units: list[Unit] = []
        self.proj: list[Proj] = []
        self.parts: list[dict[str, Any]] = []
        self.time = 0.0
        self.over = False
        self.winner: Optional[int] = None
        self.nA = self.nB = 0
        self.aliveA = self.aliveB = 0
        self.lite = False
        self.pickups_on = pickups
        self.nn_eval_time = 0.0
        self.shake_t = 0.0
        self.shake_mag = 0.0

        if new_map or breeder.terrain is None:
            breeder.terrain = self.gen_terrain(breeder.biome_key, breeder.preset_key)
            breeder.map_id += 1
        self.terrain = breeder.terrain
        self.map_id = breeder.map_id
        self.biome_name = BIOMES[breeder.biome_key]["name"]
        self.preset_name = LEVEL_PRESETS[breeder.preset_key]["name"]
        self.pas = [[TERRAIN[t].pas for t in col] for col in self.terrain]

        self._sdiv = 8.0
        self._ddiv = 12.0
        self._sr2 = 16.0
        self.flash = 0.0

        self.pickups: list[list[Any]] = []
        if pickups:
            for _ in range(6):
                for _try in range(30):
                    x = random.uniform(4, COLS - 5); y = random.uniform(0.6, ROWS - 0.6)
                    if self.pas[int(x)][int(y)] and all((pk[1]-x)**2+(pk[2]-y)**2 > 2.2 for pk in self.pickups):
                        self.pickups.append([random.choice(PICKUP_KINDS), x, y])
                        break

        specs: list[list[str]] = [[], []]
        for (team, key), cnt in counts.items():
            specs[team] += [key] * cnt
        self.nA = len(specs[0]); self.nB = len(specs[1])
        self.aliveA = self.nA; self.aliveB = self.nB

        for team in (0, 1):
            pos = self.formation_positions(team, specs[team])
            for key, (x, y) in zip(specs[team], pos):
                genome, elite = breeder.get_genome((team, key))
                self.units.append(Unit(self, team, key, x, y, genome, elite))
                self.add_part("✨", x, y, 0.35)

        self.init_hp = [sum(u.max_hp for u in self.units if u.team == 0),
                        sum(u.max_hp for u in self.units if u.team == 1)]

        self.grid = SGrid()
        self._au: list[Unit] = []
        self._ax: list[float] = []
        self._ay: list[float] = []
        self._ateam: list[int] = []
        self._ahp: list[float] = []
        self._ahpm: list[float] = []

    def formation_positions(self, team: int, keys: list[str]) -> list[tuple[float, float]]:
        n = len(keys)
        if n == 0: return []
        front = 2.4 if team == 0 else COLS - 2.6
        back  = 1.4 if team == 0 else COLS - 1.6
        apex  = 2.9 if team == 0 else COLS - 2.9
        dirn  = 1 if team == 0 else -1

        def even(count: int, y0: float = 0.9, y1: float = ROWS - 0.9) -> list[float]:
            if count <= 0: return []
            if count == 1: return [ROWS / 2]
            return [y0 + (y1 - y0) * i / (count - 1) for i in range(count)]

        if self.formation == "line":
            return [(front, y) for y in even(n)]
        if self.formation == "wall":
            back_keys  = [k for k in keys if TYPE_BY_KEY[k].ranged or TYPE_BY_KEY[k].heal_power]
            melee_keys = [k for k in keys if k not in back_keys]
            return [(back, y) for y in even(len(back_keys))] + [(front, y) for y in even(len(melee_keys))]
        if self.formation == "wedge":
            pts = []
            for i in range(n):
                col = i // 2; side = 1 if i % 2 else -1
                x = apex - dirn * col * 0.85
                y = ROWS / 2 + side * col * 1.15
                pts.append((clamp(x, 0.7, COLS - 0.7), clamp(y, 0.7, ROWS - 0.7)))
            return pts
        if self.formation == "spread":
            xr = (1.0, 2.6) if team == 0 else (COLS - 2.8, COLS - 1.2)
            pts = []
            for _ in range(n):
                best = None; score = -1.0
                for _try in range(24):
                    x = random.uniform(*xr); y = random.uniform(0.7, ROWS - 0.7)
                    s = min((((x-px)**2 + (y-py)**2) for px, py in pts), default=99.0)
                    if s > score: score = s; best = (x, y)
                pts.append(best)
            return pts
        return [(random.uniform(1.0, 2.6) if team == 0 else random.uniform(COLS - 2.8, COLS - 1.2),
                 random.uniform(0.8, ROWS - 0.8)) for _ in range(n)]

    def gen_terrain(self, biome_key: str = "plains", preset_key: str = "classic") -> list[list[str]]:
        biome = BIOMES[biome_key]
        preset = LEVEL_PRESETS[preset_key]
        g = [[biome["base"]] * ROWS for _ in range(COLS)]

        path_tiles: set[tuple[int, int]] = set()
        n_paths = preset.get("paths", 3)
        for _ in range(n_paths):
            y = random.randint(2, ROWS - 3)
            for x in range(3, COLS - 2):
                path_tiles.add((x, y))
                y = int(clamp(y + random.choice([-1, 0, 0, 1]), 0, ROWS - 1))

        def set_tile(x: int, y: int, kind: str) -> None:
            if 3 <= x < COLS - 3 and 0 <= y < ROWS:
                if (x, y) in path_tiles and kind in ("water", "rock", "wall"):
                    return
                g[x][y] = kind
                mx = COLS - 1 - x
                if 3 <= mx < COLS - 3:
                    if (mx, y) in path_tiles and kind in ("water", "rock", "wall"):
                        return
                    g[mx][y] = kind

        def feature(kind: str, count: int, size: int) -> None:
            for _ in range(count):
                x = random.randint(4, COLS // 2 - 1)
                y = random.randint(1, ROWS - 2)
                for _ in range(size):
                    set_tile(x, y, kind)
                    if random.random() < 0.5:
                        set_tile(x + 1, y, kind)
                    if random.random() < 0.5:
                        set_tile(x, y + 1, kind)
                    dx, dy = random.choice([(0, 1), (0, -1), (1, 0), (-1, 0),
                                            (1, 1), (-1, -1), (1, -1), (-1, 1)])
                    x = clamp(x + dx, 3, COLS // 2 - 1)
                    y = clamp(y + dy, 1, ROWS - 2)

        scale = preset.get("features_scale", 1.0)
        for feat in biome["features"]:
            kind, count, size = feat
            feature(kind, int(count * scale), size)

        if preset.get("extra_water"):
            feature("water", 3, 10)
            for x in range(3, COLS - 3):
                for y in range(ROWS):
                    if y < 1 or y > ROWS - 2:
                        if (x, y) not in path_tiles:
                            g[x][y] = "water"

        for x in range(COLS):
            if x < 3 or x >= COLS - 3:
                for y in range(ROWS):
                    g[x][y] = biome["base"]

        return g

    def update_tile(self, u: Unit) -> None:
        if u.fly: return
        name = self.terrain[clamp(int(u.x), 0, COLS - 1)][clamp(int(u.y), 0, ROWS - 1)]
        if name == u.tname: return
        u.tname = name
        tt = TERRAIN[name]
        u.tsp, u.tdf, u.theal = tt.speed, tt.df, tt.heal
        u.tdot = 0.0 if (name == "lava" and u.t.lava_immune) else tt.dot
        u.tslip = tt.slip

    def passable_at(self, x: float, y: float, u: Unit) -> bool:
        if u is not None and (u.fly or u.phase): return True
        return self.pas[clamp(int(x), 0, COLS - 1)][clamp(int(y), 0, ROWS - 1)]

    def move_unit(self, u: Unit, dx: float, dy: float) -> None:
        nx = clamp(u.x + dx, 0.35, COLS - 0.35)
        if self.passable_at(nx, u.y, u): u.x = nx
        ny = clamp(u.y + dy, 0.35, ROWS - 0.35)
        if self.passable_at(u.x, ny, u): u.y = ny
        self.update_tile(u)

    def add_part(self, ch: str, x: float, y: float, ttl: float, scale: float = 0.7) -> None:
        if len(self.parts) < MAX_PARTS:
            self.parts.append({"kind": "emoji", "ch": ch, "x": x, "y": y, "ttl": ttl, "life": ttl, "scale": scale})

    def add_text(self, x: float, y: float, txt: str, col: str, scale: float = 0.42, ttl: float = 0.7) -> None:
        if len(self.parts) < MAX_PARTS:
            self.parts.append({"kind": "text", "txt": txt, "x": x, "y": y - 0.45, "ttl": ttl, "life": ttl, "col": col, "scale": scale})

    def add_ring(self, x: float, y: float, target_r: float, col: str, ttl: float = 0.3) -> None:
        if len(self.parts) < MAX_PARTS:
            self.parts.append({"kind": "ring", "x": x, "y": y, "r": 0.2, "tr": target_r, "ttl": ttl, "life": ttl, "col": col})

    def add_dmg(self, x: float, y: float, txt: str, col: str, scale: float = 0.42, ttl: float = 0.7) -> None:
        if not self.lite: self.add_text(x, y, txt, col, scale, ttl)

    def add_shake(self, mag: float, dur: float) -> None:
        if not self.lite:
            self.shake_t = max(self.shake_t, dur)
            self.shake_mag = max(self.shake_mag, mag)

    def kill(self, t: Unit, src: Optional[Unit]) -> None:
        if t.t.revive and not t.used_revive:
            t.used_revive = True
            t.hp = t.max_hp * 0.5
            t.cd = 0.8
            self.add_text(t.x, t.y - 0.5, "🌅 REBORN!", "#ffb347", 0.55, 1.2)
            self.add_part("🔥", t.x, t.y, 0.6, 0.9)
            self.add_part("✨", t.x, t.y, 0.5)
            return
        t.alive = False; t.hp = 0; t.streak = 0
        t.fade_t = 0.4
        if t.team == 0: self.aliveA -= 1
        else: self.aliveB -= 1
        if src is not None and src.alive:
            src.fit_kills += 1
            src.streak += 1
            s = src.streak
            if s == 2: self.add_text(src.x, src.y - 0.8, "⚡ DOUBLE KILL", "#ffd93d", 0.5, 1.0)
            elif s == 3: self.add_text(src.x, src.y - 0.8, "🔥 TRIPLE KILL", "#ff9f43", 0.5, 1.0)
            elif s >= 4: self.add_text(src.x, src.y - 0.8, f"💀 x{s} RAMPAGE", "#ff6b6b", 0.55, 1.0)
        self.add_part("💀", t.x, t.y, 1.5)
        ex = t.t.explode
        if ex:
            dmg, rad = ex
            self.add_part("💥", t.x, t.y, 0.5, 1.1)
            self.add_ring(t.x, t.y, rad, "#ff6b6b", 0.3)
            self.add_shake(0.5, 0.2)
            self.flash = max(self.flash, 0.15)
            r2 = rad * rad
            for o in self.grid.nearby(t.x, t.y, rad):
                if o.alive and o.team != t.team and (o.x - t.x) ** 2 + (o.y - t.y) ** 2 < r2:
                    self.apply_damage(o, dmg, t)

    def apply_damage(self, t: Unit, raw: float, src: Optional[Unit], crit: bool = False) -> float:
        if not t.alive: return 0.0
        dmg = raw * t.tdf * t.t.armor
        if t.buff_shd_t > 0: dmg *= 0.6
        t.hp -= dmg
        t.flash = 0.12
        if src is not None: src.fit_dmg += dmg
        if crit:
            self.add_dmg(t.x, t.y, f"💥-{dmg:.0f}", "#ffd93d", 0.55, 0.9)
            self.add_shake(0.2, 0.1)
        else:
            self.add_dmg(t.x, t.y, f"-{dmg:.0f}", "#ff6b6b")
        if t.hp <= 0: self.kill(t, src)
        return dmg

    def apply_poison(self, t: Unit, dps: float, dur: float, src: Unit) -> None:
        if t.alive and dps >= (t.poison_dps if t.poison_t > 0 else 0.0):
            t.poison_t = dur; t.poison_dps = dps; t.poison_src = src

    def do_attack(self, u: Unit, t: Unit) -> None:
        u.cd = u.t.cd
        crit = random.random() < u.t.crit
        if u.t.ranged:
            dx = t.x - u.x
            dy = t.y - u.y
            dist = math.hypot(dx, dy) or 1e-6
            time_to_hit = dist / u.t.proj_speed
            tx_pred = t.x + t.mvx * t.t.speed * time_to_hit
            ty_pred = t.y + t.mvy * t.t.speed * time_to_hit
            
            pr = Proj(u, tx_pred, ty_pred)
            pr.crit = crit
            self.proj.append(pr)
            if crit: self.add_part("✨", u.x, u.y, 0.3)
        else:
            d = math.hypot(t.x - u.x, t.y - u.y) or 1e-6
            u.lunge_t = 0.16; u.lx = (t.x - u.x) / d; u.ly = (t.y - u.y) / d
            dealt = self.apply_damage(t, u.t.atk * (1.8 if crit else 1.0), u, crit)
            if crit: self.add_part("✨", t.x, t.y, 0.3)
            
            # Dynamic Knockback
            if not t.fly:
                kb = 0.15 * (1.5 if crit else 1.0)
                nx = clamp(t.x + (t.x - u.x)/d * kb, 0.35, COLS - 0.35)
                if self.passable_at(nx, t.y, t): t.x = nx
                ny = clamp(t.y + (t.y - u.y)/d * kb, 0.35, ROWS - 0.35)
                if self.passable_at(t.x, ny, t): t.y = ny
                
            ls = u.t.lifesteal
            if ls and dealt > 0:
                heal = dealt * ls
                u.hp = min(u.max_hp, u.hp + heal)
                if heal >= 3: self.add_dmg(u.x, u.y, f"🩸+{heal:.0f}", "#ff9ecd", 0.40, 0.6)
            po = u.t.poison
            if po and dealt > 0: self.apply_poison(t, po[0], po[1], u)

    def pickup(self, u: Unit, pk: list[Any]) -> None:
        kind = pk[0]
        self.add_part("✨", pk[1], pk[2], 0.4)
        if kind == "🧪":
            amt = min(40, u.max_hp - u.hp)
            if amt > 0: u.hp += amt
            self.add_text(u.x, u.y, f"🧪+{amt:.0f}", "#57e389")
        elif kind == "💰":
            u.fit_gold += 60
            self.add_text(u.x, u.y, "💰+60", "#ffd93d")
        elif kind == "⚡":
            u.buff_spd_t = 6.0
            self.add_text(u.x, u.y, "⚡ ZOOM!", "#ffe66d")
        else:
            u.buff_shd_t = 6.0
            self.add_text(u.x, u.y, "🛡️ SHIELD!", "#7fd4ff")

    def step(self, dt: float) -> None:
        if dt > 0.04:
            steps = math.ceil(dt / 0.04)
            sub_dt = dt / steps
            for _ in range(steps):
                self._step(sub_dt)
        else:
            self._step(dt)
            
    def _step(self, dt: float) -> None:
        self.time += dt
        heal_m = 1.0
        dot_m = 1.0

        au: list[Unit] = []; axs: list[float] = []; ays: list[float] = []
        at: list[int] = []; ah: list[float] = []; am: list[float] = []
        
        # Update display HP and fade timers for ALL units
        for u in self.units:
            if u.alive:
                u.disp_hp += (u.hp - u.disp_hp) * min(1.0, dt * 10.0)
            elif u.fade_t > 0:
                u.fade_t -= dt
                
        for u in self.units:
            if u.alive:
                u._ai = len(au)
                au.append(u); axs.append(u.x); ays.append(u.y)
                at.append(u.team); ah.append(u.hp); am.append(u.max_hp)
        self._au = au; self._ax = axs; self._ay = ays
        self._ateam = at; self._ahp = ah; self._ahpm = am
        n = len(au)
        self.grid.build(au)

        due: list[Unit] = []
        for u in au:
            u.cd = max(0.0, u.cd - dt)
            u.flash = max(0.0, u.flash - dt)
            u.lunge_t = max(0.0, u.lunge_t - dt)
            if u.buff_spd_t > 0: u.buff_spd_t -= dt
            if u.buff_shd_t > 0: u.buff_shd_t -= dt
            if u.theal: u.hp = min(u.max_hp, u.hp + u.theal * heal_m * dt)
            if u.tdot > 0:
                u.hp -= u.tdot * dot_m * dt
                if u.hp <= 0:
                    self.kill(u, None)
                    continue
            if u.poison_t > 0:
                u.poison_t -= dt
                d = u.poison_dps * dt
                u.hp -= d
                if u.poison_src is not None: u.poison_src.fit_dmg += d
                if u.hp <= 0:
                    self.kill(u, u.poison_src)
                    continue
            
            if u.target is not None and u.target.alive:
                if math.hypot(u.target.x - u.x, u.target.y - u.y) < 10.0:
                    u.fit_time += dt
            u.think_t -= dt
            if u.think_t <= 0.0:
                due.append(u)
                u.think_t = 0.10 + random.random() * 0.04
        if due:
            ins = [u.sense() for u in due]
            t_nn_start = time.perf_counter()
            outs, hids = forward_batch([(u.nn, i) for u, i in zip(due, ins)])
            self.nn_eval_time = time.perf_counter() - t_nn_start
            for u, i_, o, h in zip(due, ins, outs, hids):
                u.set_action(i_, o, h)

        for a in au:
            if not a.alive: continue
            for b in self.grid.nearby(a.x, a.y, 0.8):
                if b is a or not b.alive or id(b) <= id(a): continue
                dx = b.x - a.x; dy = b.y - a.y
                d2 = dx * dx + dy * dy
                if 1e-9 < d2 < 0.49:
                    d = math.sqrt(d2)
                    push = (0.7 - d) * dt * 6.0
                    nx, ny = dx / d, dy / d
                    a.x -= nx * push; a.y -= ny * push
                    b.x += nx * push; b.y += ny * push
                elif d2 <= 1e-9:
                    a.x -= 0.05; a.y -= 0.05

        for u in au:
            if not u.alive: continue

            bx, by = u.mvx, u.mvy
            sx, sy, tw = 0.0, 0.0, 1.0

            if u.pickup_mode > 0.5 and self.pickups:
                best_pk = None; best_d2 = 1e18
                for pk in self.pickups:
                    d2 = (pk[1] - u.x)**2 + (pk[2] - u.y)**2
                    if d2 < best_d2: best_d2 = d2; best_pk = pk
                if best_pk and best_d2 < 100.0:
                    dx = best_pk[1] - u.x; dy = best_pk[2] - u.y
                    d = math.hypot(dx, dy) or 1e-6
                    w = (u.pickup_mode - 0.5) * 2
                    sx += w * (dx / d); sy += w * (dy / d); tw += w

            if u.flee_mode > 0.5 and u.hp < u.max_hp * 0.55 and u.target and u.target.alive:
                dx = u.x - u.target.x; dy = u.y - u.target.y
                d = math.hypot(dx, dy) or 1e-6
                w = (u.flee_mode - 0.5) * 2
                sx += w * (dx / d); sy += w * (dy / d); tw += w

            if u.kite_mode > 0.5 and u.t.ranged and u.target and u.target.alive:
                dx = u.x - u.target.x; dy = u.y - u.target.y
                d = math.hypot(dx, dy) or 1e-6
                w = (u.kite_mode - 0.5) * 2
                if d < u.t.rng * 0.8:
                    sx += w * (dx / d); sy += w * (dy / d); tw += w
                elif d > u.t.rng * 1.1:
                    sx += w * (-dx / d); sy += w * (-dy / d); tw += w

            if u.formation_mode > 0.5:
                best = None; bd = 1e18
                for o in self.grid.nearby(u.x, u.y, 4.0):
                    if o is not u and o.alive and o.team == u.team:
                        d2 = (o.x - u.x)**2 + (o.y - u.y)**2
                        if d2 < bd: bd = d2; best = o
                if best:
                    w = (u.formation_mode - 0.5) * 2
                    if bd > 2.5:
                        dx = best.x - u.x; dy = best.y - u.y
                        d = math.hypot(dx, dy) or 1e-6
                        sx += w * (dx / d); sy += w * (dy / d); tw += w
                    elif bd < 1.0:
                        dx = u.x - best.x; dy = u.y - best.y
                        d = math.hypot(dx, dy) or 1e-6
                        sx += w * 0.5 * (dx / d); sy += w * 0.5 * (dy / d); tw += w * 0.5

            if u.roam_mode > 0.5 and not (u.target and u.target.alive):
                dx = COLS/2 - u.x; dy = ROWS/2 - u.y
                d = math.hypot(dx, dy) or 1e-6
                w = (u.roam_mode - 0.5) * 2
                sx += w * (dx / d); sy += w * (dy / d); tw += w

            dodge_x, dodge_y, dodge_w = 0.0, 0.0, 0.0
            for pr in self.proj:
                if pr.team != u.team:
                    dx = u.x - pr.x
                    dy = u.y - pr.y
                    dist = math.hypot(dx, dy)
                    if dist < 4.0:
                        pr_speed = math.hypot(pr.vx, pr.vy)
                        if pr_speed > 1e-6:
                            dot = (pr.vx * dx + pr.vy * dy) / (dist * pr_speed)
                            if dot > 0.8:
                                time_to_impact = dist / pr_speed
                                if time_to_impact < 1.0:
                                    pdx = -pr.vy / pr_speed
                                    pdy = pr.vx / pr_speed
                                    sign = 1 if (pdx * u.mvx + pdy * u.mvy) > 0 else -1
                                    w = 2.5 * (1.0 - time_to_impact)
                                    dodge_x += sign * pdx * w
                                    dodge_y += sign * pdy * w
                                    dodge_w += w
            if dodge_w > 0:
                dl = math.hypot(dodge_x, dodge_y)
                if dl > 1e-6:
                    sx += (dodge_x / dl) * min(dodge_w, 2.5)
                    sy += (dodge_y / dl) * min(dodge_w, 2.5)
                    tw += min(dodge_w, 2.5)

            if u.hp < u.max_hp * 0.35 and not u.fly:
                nearest_healer = None
                hd = 1e18
                for ally in self.grid.nearby(u.x, u.y, 10.0):
                    if ally.team == u.team and ally.alive and (ally.t.heal_power or 0) > 0:
                        d2 = (ally.x - u.x)**2 + (ally.y - u.y)**2
                        if d2 < hd: hd = d2; nearest_healer = ally
                if nearest_healer:
                    dx = nearest_healer.x - u.x; dy = nearest_healer.y - u.y
                    d = math.hypot(dx, dy) or 1e-6
                    w = 1.5
                    sx += w * (dx / d); sy += w * (dy / d); tw += w

            if not u.fly and not u.phase:
                ax = ay = 0.0
                ix, iy = int(u.x), int(u.y)
                for ddx in (-1, 0, 1):
                    for ddy in (-1, 0, 1):
                        if ddx == 0 and ddy == 0: continue
                        nx = clamp(ix + ddx, 0, COLS - 1)
                        ny = clamp(iy + ddy, 0, ROWS - 1)
                        tname = self.terrain[nx][ny]
                        tt = TERRAIN[tname]
                        is_hazard = (not tt.pas) or (tt.dot > 0 and not u.t.lava_immune)
                        if is_hazard:
                            dx = u.x - (nx + 0.5); dy = u.y - (ny + 0.5)
                            d2 = dx*dx + dy*dy
                            if 1e-6 < d2 < 2.5:
                                d = math.sqrt(d2)
                                push = 1.5 if tt.dot > 0 else 0.9
                                ax += (dx / (d * d)) * push
                                ay += (dy / (d * d)) * push
                al = math.hypot(ax, ay)
                if al > 1e-3:
                    sx += ax / al; sy += ay / al; tw += 1.2

            fx = (bx + sx) / tw
            fy = (by + sy) / tw
            fl = math.hypot(fx, fy)
            if fl > 1e-3:
                u.mvx = fx / fl; u.mvy = fy / fl
            else:
                u.mvx = 0.0; u.mvy = 0.0

            spd = u.t.speed * (1.35 if u.buff_spd_t > 0 else 1.0)
            if u.defensive_mode > 0.5:
                spd *= 0.5

            if u.tslip:
                u.slipx += u.mvx * 10.0 * spd * dt
                u.slipy += u.mvy * 10.0 * spd * dt
                cap = spd * 1.6
                l = math.hypot(u.slipx, u.slipy)
                if l > cap:
                    u.slipx *= cap / l; u.slipy *= cap / l
                fr = max(0.0, 1.0 - dt * 0.6)
                u.slipx *= fr; u.slipy *= fr
            else:
                fr = max(0.0, 1.0 - dt * 8.0)
                u.slipx *= fr; u.slipy *= fr
            self.move_unit(u, (u.mvx * spd * u.tsp + u.slipx) * dt,
                              (u.mvy * spd * u.tsp + u.slipy) * dt)

            heal_p = u.t.heal_power or 0
            if heal_p:
                pure = u.t.atk == 0
                if u.cd <= 0.0 and u.gate > (0.30 if pure else 0.40):
                    bi = -1; bd = 1e18
                    best_priority = -1.0
                    rng2 = (u.t.rng + 0.2) ** 2
                    for j in range(n):
                        if at[j] == u.team and au[j] is not u and au[j].alive:
                            hp_ratio = ah[j] / am[j]
                            if hp_ratio < 0.97:
                                priority = (1.0 - hp_ratio) + (1.0 / (1.0 + (axs[j] - u.x)**2 + (ays[j] - u.y)**2))
                                if priority > best_priority:
                                    dx = axs[j] - u.x; dy = ays[j] - u.y
                                    d2 = dx * dx + dy * dy
                                    if d2 <= rng2:
                                        best_priority = priority
                                        bi = j
                                        bd = d2
                    if bi >= 0:
                        best = au[bi]
                        u.cd = u.t.cd
                        amt = min(best.max_hp - best.hp, heal_p)
                        best.hp += amt; u.fit_heal += amt
                        self.add_dmg(best.x, best.y, f"💚+{amt:.0f}", "#57e389")
                        self.add_part("💚", best.x, best.y - 0.3, 0.5)
                        continue
                if pure:
                    bi_s = -1; best_priority_s = -1.0
                    for j in range(n):
                        if at[j] == u.team and au[j] is not u and au[j].alive:
                            hp_ratio = ah[j] / am[j]
                            if hp_ratio < 0.97:
                                priority = (1.0 - hp_ratio)
                                if priority > best_priority_s:
                                    best_priority_s = priority
                                    bi_s = j
                    if bi_s >= 0:
                        dx = axs[bi_s] - u.x; dy = ays[bi_s] - u.y
                        d = math.hypot(dx, dy) or 1e-6
                        u.mvx = u.mvx * 0.3 + (dx / d) * 0.7
                        u.mvy = u.mvy * 0.3 + (dy / d) * 0.7
                        l = math.hypot(u.mvx, u.mvy)
                        if l > 1e-3: u.mvx /= l; u.mvy /= l
                    continue

            t = u.target
            if t is not None and t.alive and u.cd <= 0.0 and u.gate > 0.35:
                if math.hypot(t.x - u.x, t.y - u.y) <= u.t.rng + 0.2:
                    self.do_attack(u, t)

        for pk in self.pickups[:]:
            for u in self.grid.nearby(pk[1], pk[2], 0.8):
                if u.alive and (u.x - pk[1]) ** 2 + (u.y - pk[2]) ** 2 < 0.3:
                    self.pickup(u, pk)
                    self.pickups.remove(pk)
                    break

        surv: list[Proj] = []
        for pr in self.proj:
            pr.x += pr.vx * dt; pr.y += pr.vy * dt; pr.ttl -= dt
            hit: Optional[Unit] = None
            for o in self.grid.nearby(pr.x, pr.y, 0.45):
                if o.alive and o.team != pr.team and (o.x - pr.x) ** 2 + (o.y - pr.y) ** 2 < 0.18:
                    hit = o; break
            if hit is not None:
                mult = 1.8 if pr.crit else 1.0
                self.apply_damage(hit, pr.dmg * mult, pr.src, pr.crit)
                self.add_part("💥", pr.x, pr.y, 0.3)
                if pr.splash:
                    self.add_ring(pr.x, pr.y, 1.2, "#add8e6", 0.3)
                    for o in self.grid.nearby(pr.x, pr.y, 1.2):
                        if o.alive and o.team != pr.team and o is not hit and (o.x - pr.x) ** 2 + (o.y - pr.y) ** 2 < 1.4:
                            self.apply_damage(o, pr.dmg * 0.45, pr.src)
            elif pr.ttl > 0:
                surv.append(pr)
        self.proj = surv

        if self.parts:
            keep: list[dict[str, Any]] = []
            for pa in self.parts:
                pa["ttl"] -= dt
                if pa["ttl"] > 0:
                    if pa["kind"] == "text": pa["y"] -= dt * 1.4
                    elif pa["kind"] == "ring": 
                        pa["r"] += (pa["tr"] - pa["r"]) * min(1.0, dt * 12.0)
                    keep.append(pa)
            self.parts = keep

        self.flash = max(0.0, self.flash - dt * 1.5)
        
        if self.shake_t > 0:
            self.shake_t -= dt
            if self.shake_t <= 0:
                self.shake_mag = 0.0

        self.check_end()

    def check_end(self) -> None:
        if self.over: return
        a0 = self.aliveA > 0; a1 = self.aliveB > 0
        if not a0 and not a1: w = None
        elif not a1: w = 0
        elif not a0: w = 1
        elif self.time >= self.limit:
            hpA = sum(u.hp for u in self.units if u.team == 0 and u.alive)
            hpB = sum(u.hp for u in self.units if u.team == 1 and u.alive)
            maxA = max(1, self.init_hp[0])
            maxB = max(1, self.init_hp[1])
            pctA = hpA / maxA
            pctB = hpB / maxB
            if pctA > pctB * 1.05:
                w = 0
            elif pctB > pctA * 1.05:
                w = 1
            else:
                w = None
        else: return
        self.winner = w; self.over = True

    def finalize(self) -> dict[tuple[int, str], list[tuple[list[float], float]]]:
        results: dict[tuple[int, str], list[tuple[list[float], float]]] = {}
        for u in self.units:
            f = (u.fit_dmg + 80.0 * u.fit_kills + 5.0 * u.fit_time
                 + 0.5 * u.hp + 1.0 * u.fit_heal + u.fit_gold)
            if self.winner is not None:
                if u.team == self.winner:
                    time_bonus = max(0.0, (self.limit - self.time) * 4.0)
                    f += 200.0 + time_bonus + (120.0 if u.alive else 0.0)
                else:
                    f -= 60.0
            else:
                f += (40.0 if u.alive else 0.0) + u.fit_dmg * 0.2
            results.setdefault((u.team, u.t.key), []).append((u.genome, f))
        return results

# ----------------------------- Genetic Algorithm -----------------------------
@dataclass
class GAConfig:
    mut_rate: float = 0.15
    mut_strength: float = 0.35
    crossover: float = 0.7
    elites: int = 1

def tournament(items: list[tuple[list[float], float]], k: int = 3) -> list[float]:
    best: Optional[tuple[list[float], float]] = None
    for _ in range(k):
        it = random.choice(items)
        if best is None or it[1] > best[1]: best = it
    return best[0]

def crossover(g1: list[float], g2: list[float]) -> list[float]:
    return [a if random.random() < 0.5 else b for a, b in zip(g1, g2)]

def mutate(g: list[float], cfg: GAConfig) -> None:
    mr = cfg.mut_rate; ms = cfg.mut_strength
    for i in range(len(g)):
        r = random.random()
        if r < mr: g[i] += random.gauss(0, ms)
        elif r < mr + 0.01: g[i] = random.uniform(-1.5, 1.5)
        g[i] = clamp(g[i], -4, 4)

def breed_population(items: list[tuple[list[float], float]], count: int, cfg: GAConfig) -> list[list[float]]:
    out: list[list[float]] = []
    while len(out) < count:
        if len(items) >= 2 and random.random() < cfg.crossover:
            g = crossover(tournament(items), tournament(items))
        elif items:
            g = list(tournament(items))
        else:
            g = random_genome()
        mutate(g, cfg)
        out.append(g)
    return out

class Breeder:
    def __init__(self, cfg: GAConfig) -> None:
        self.cfg = cfg
        self.pools: dict[tuple[int, str], dict[str, list[tuple[list[float], bool]]]] = {}
        self.hof: dict[tuple[int, str], tuple[list[float], float]] = {}
        self.terrain: Optional[list[list[str]]] = None
        self.map_id = 0
        self.biome_key = "plains"
        self.preset_key = "classic"
        self.stagnation: dict[int, int] = {0: 0, 1: 0}
        self.last_best: dict[int, float] = {0: -1e9, 1: -1e9}
        self.ga_time = 0.0

    def get_genome(self, key: tuple[int, str]) -> tuple[list[float], bool]:
        p = self.pools.get(key)
        if p and p["next"]: return p["next"].pop(0)
        h = self.hof.get(key)
        if h is not None:
            g = [clamp(x + random.gauss(0, 0.05), -4, 4) for x in h[0]]
            return g, False
        return random_genome_for_type(key[1]), False

    def evolve(self, results: dict[tuple[int, str], list[tuple[list[float], float]]],
               counts: dict[tuple[int, str], int]) -> dict[int, tuple[str, float]]:
        t_ga_start = time.perf_counter()
        best: dict[int, tuple[str, float]] = {}
        for key, items in results.items():
            items.sort(key=lambda it: -it[1])
            h = self.hof.get(key)
            if h is None or items[0][1] > h[1]:
                self.hof[key] = (list(items[0][0]), items[0][1])
            team = key[0]
            current_best = items[0][1]
            if current_best > self.last_best[team] + 1.0:
                self.last_best[team] = current_best
                self.stagnation[team] = 0
            else:
                self.stagnation[team] += 1
            n_elite = min(self.cfg.elites, len(items))
            pool = [(list(items[i][0]), True) for i in range(n_elite)]
            n_breed = max(0, counts.get(key, 0) - n_elite)
            if self.stagnation[team] >= 4:
                n_random = max(1, n_breed // 3)
                n_breed -= n_random
                pool += [(random_genome_for_type(key[1]), False) for _ in range(n_random)]
                for i in range(n_elite):
                    mutated_elite = list(items[i][0])
                    mutate(mutated_elite, GAConfig(mut_rate=self.cfg.mut_rate * 2, mut_strength=self.cfg.mut_strength * 2))
                    pool.append((mutated_elite, False))
            pool += [(g, False) for g in breed_population(items, n_breed, self.cfg)]
            self.pools[key] = {"next": pool}
            if team not in best or items[0][1] > best[team][1]:
                best[team] = (key[1], items[0][1])
        self.ga_time = time.perf_counter() - t_ga_start
        return best

    def reset(self) -> None:
        self.pools = {}; self.hof = {}; self.terrain = None; self.map_id = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "pools": {f"{t}|{k}": [list(g) for g, _ in v["next"]] for (t, k), v in self.pools.items()},
            "hof":   {f"{t}|{k}": [list(g), f] for (t, k), (g, f) in self.hof.items()},
        }

    def from_dict(self, d: dict[str, Any]) -> None:
        self.pools = {}
        for s, genomes in d.get("pools", {}).items():
            t, k = s.split("|")
            glen = genome_len_for_type(k)
            gs = [list(g) for g in genomes if len(g) == glen]
            if gs:
                self.pools[(int(t), k)] = {"next": [(g, False) for g in gs]}
        self.hof = {}
        for s, item in d.get("hof", {}).items():
            t, k = s.split("|")
            g, f = item
            if len(g) == genome_len_for_type(k):
                self.hof[(int(t), k)] = (list(g), float(f))
        self.terrain = None

# ----------------------------- UI Widgets -----------------------------
class BrainWidget(QWidget):
    def __init__(self, win: "MainWindow") -> None:
        super().__init__()
        self.win = win
        self.setMinimumHeight(190)

    def paintEvent(self, _: Any) -> None:
        p = QPainter(self)
        p.fillRect(self.rect(), QColor("#0b0e13"))
        win = self.win
        u = win.sel_unit
        W, H = self.width(), self.height()

        if u is None:
            p.setFont(text_font(12)); p.setPen(QPen(QColor("#7d8794")))
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter,
                       "🧠 Click any unit on the battlefield to watch its brain fire in real time!\n"
                       "🟦 positive activation · 🟥 negative · thicker line = stronger signal")
            return

        head = (f"{u.t.emoji} {u.t.name} {'👑' if u.elite else ''} · "
                f"{'🟦 Blue' if u.team == 0 else '🟥 Red'}")
        if not u.alive:
            head += f"   💀 fell at {u.fit_time:.1f}s — its genome lives on in its children"
        p.setFont(text_font(12)); p.setPen(QPen(QColor("#e8edf2")))
        p.drawText(QPointF(10, 16), head)

        if u.a_in is None or not u.alive:
            p.setPen(QPen(QColor("#7d8794"))); p.setFont(text_font(11))
            p.drawText(self.rect().adjusted(0, 10, 0, 10), Qt.AlignmentFlag.AlignCenter, "🤔 …" if u.a_in is None else "💀")
            return

        wb = win.battle
        stats = (f"❤️{u.hp:.0f}/{u.max_hp}   🗡️{u.fit_dmg:.0f}   ⚰️{u.fit_kills}   "
                 f"💚{u.fit_heal:.0f}   💰{u.fit_gold:.0f}")
        p.drawText(QPointF(10, 31), stats)

        top = 42; span = H - top - 14
        xs = (24, W * 0.50, W - 50)
        nh = u.nn.nh
        def py(i: int, n_: int) -> float:
            return top + span * i / (n_ - 1) if n_ > 1 else top + span / 2
        pin  = [(xs[0], py(i, N_IN))  for i in range(N_IN)]
        phid = [(xs[1], py(i, nh))   for i in range(nh)]
        pout = [(xs[2], py(i, N_OUT)) for i in range(N_OUT)]

        w = u.nn.w
        k1, k2 = u.nn.k1, u.nn.k2
        order = sorted(range(k1), key=lambda k: -abs(w[k]))[:70]
        for k in order:
            h, i = divmod(k, N_IN)
            self._conn(p, pin[i], phid[h], w[k], u.a_in[i])
        for o in range(N_OUT):
            for h in range(nh):
                k = k2 + o * nh + h
                self._conn(p, phid[h], pout[o], w[k], u.a_hid[h])

        def acol(a: float) -> QColor:
            t = (clamp(a, -1, 1) + 1) / 2
            return QColor(int(255 - 159 * t), int(96 + 74 * t), int(96 + 159 * t))

        p.setPen(Qt.PenStyle.NoPen)
        for i, (cx, cy) in enumerate(pin):
            p.setBrush(acol(u.a_in[i])); p.drawEllipse(QPointF(cx, cy), 3.2, 3.2)
        for i, (cx, cy) in enumerate(phid):
            p.setBrush(acol(u.a_hid[i])); p.drawEllipse(QPointF(cx, cy), 4.0, 4.0)

        labs = ("➡️ X", "⬆️ Y", "⚔️ Act", "🎯 Tgt", "🏃 Flee", "🎁 Loot", "🧭 Roam", "🛡️ Def", "🤝 Form", "🏹 Kite")
        p.setFont(text_font(10))
        for i, (cx, cy) in enumerate(pout):
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(acol(u.a_out[i])); p.drawEllipse(QPointF(cx, cy), 5.0, 5.0)
            p.setPen(QPen(QColor("#cfd8e3")))
            p.drawText(QPointF(cx - 42, cy + 4), labs[i])
            p.drawText(QPointF(cx + 9, cy + 4), f"{u.a_out[i]:+.1f}")

        p.setFont(text_font(9)); p.setPen(QPen(QColor("#5b6673")))
        p.drawText(QPointF(6, top - 6), "👁 in")
        p.drawText(QPointF(xs[1] - 14, top - 6), "🧠 hid")
        p.drawText(QPointF(xs[2] - 18, top - 6), "🎯 out")

    def _conn(self, p: QPainter, a: tuple[float, float], b: tuple[float, float], w: float, act: float) -> None:
        sig = abs(w * act)
        col = QColor(80, 160, 255) if w > 0 else QColor(255, 110, 110)
        col.setAlpha(int(min(200, 18 + sig * 300)))
        p.setPen(QPen(col, 0.5 + min(2.0, abs(w) * 0.7)))
        p.drawLine(QPointF(a[0] + 3, a[1]), QPointF(b[0] - 4, b[1]))


class FitnessGraph(QWidget):
    def __init__(self, win: "MainWindow") -> None:
        super().__init__()
        self.win = win
        self.setMinimumHeight(140)

    def paintEvent(self, _: Any) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.fillRect(self.rect(), QColor("#0b0e13"))
        data = self.win.history[-80:]
        if len(data) < 2:
            p.setFont(text_font(12)); p.setPen(QPen(QColor("#7d8794")))
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "📈 Best fitness per team\nwill graph here after battles")
            return
        W, H = self.width(), self.height()
        pad, top = 8, 18
        pw, ph = W - pad * 2, H - top - pad
        maxv = max(1.0, max(max(b, r) for b, r in data))
        p.setFont(text_font(9))
        for i in range(4):
            y = top + ph * i / 3
            p.setPen(QPen(QColor("#232a33"), 1))
            p.drawLine(QPointF(pad, y), QPointF(W - pad, y))
            p.setPen(QPen(QColor("#5b6673")))
            p.drawText(QPointF(pad + 2, y - 2), f"{maxv * (1 - i / 3):.0f}")
        p.setFont(text_font(11))
        p.setPen(QPen(QColor("#6db3ff"))); p.drawText(QPointF(pad + 26, 13), "🟦 best")
        p.setPen(QPen(QColor("#ff7a7a"))); p.drawText(QPointF(pad + 80, 13), "🟥 best")
        n = len(data)
        for idx, col in ((0, QColor("#3d8bfd")), (1, QColor("#ff5c5c"))):
            poly = QPolygonF()
            for i, (b, r) in enumerate(data):
                v = (b, r)[idx]
                poly.append(QPointF(pad + (pw * i / (n - 1)), top + ph * (1.0 - v / maxv)))
            p.setPen(QPen(col, 2))
            p.drawPolyline(poly)


class BoardWidget(QWidget):
    def __init__(self, win: "MainWindow") -> None:
        super().__init__()
        self.win = win
        self.setMinimumSize(620, 400)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMouseTracking(True)
        self._tp: Optional[QPixmap] = None
        self._tp_key: Optional[tuple[int, int]] = None
        self._lay: Optional[tuple[int, int, int]] = None
        self._bg_spr: dict[tuple[int, int, bool], QPixmap] = {}
        self._fg_spr: dict[tuple[str, int, bool], QPixmap] = {}

    def unit_bg_sprite(self, team: int, ts: int, elite: bool) -> QPixmap:
        key = (team, ts, elite)
        pm = self._bg_spr.get(key)
        if pm is None:
            size = int(ts * 1.2)
            pm = QPixmap(size, size)
            pm.fill(QColor(0, 0, 0, 0))
            pp = QPainter(pm)
            pp.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            pp.setPen(Qt.PenStyle.NoPen)
            pp.setBrush(QColor(0, 0, 0, 70))
            pp.drawEllipse(QPointF(size / 2, size / 2 + ts * 0.25), ts * 0.35, ts * 0.12)
            grad = QRadialGradient(QPointF(size / 2, size / 2), ts * 0.5)
            c = QColor(TEAM_HEX[team])
            c.setAlpha(160)
            grad.setColorAt(0.0, c)
            c2 = QColor(TEAM_HEX[team])
            c2.setAlpha(0)
            grad.setColorAt(1.0, c2)
            pp.setBrush(grad)
            pp.drawEllipse(QPointF(size / 2, size / 2), ts * 0.5, ts * 0.5)
            if elite:
                pp.setPen(QPen(QColor("#ffd93d"), 2))
                pp.setBrush(Qt.BrushStyle.NoBrush)
                pp.drawEllipse(QPointF(size / 2, size / 2), ts * 0.48, ts * 0.48)
            pp.end()
            self._bg_spr[key] = pm
        return pm

    def unit_fg_sprite(self, tkey: str, ts: int, elite: bool) -> QPixmap:
        key = (tkey, ts, elite)
        pm = self._fg_spr.get(key)
        if pm is None:
            size = int(ts * 1.2)
            pm = QPixmap(size, size)
            pm.fill(QColor(0, 0, 0, 0))
            pp = QPainter(pm)
            pp.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            pp.setPen(QColor(255, 255, 255))
            pp.setFont(emoji_font(int(ts * 0.9)))
            pp.drawText(QRectF(0, 0, size, size), Qt.AlignmentFlag.AlignCenter, TYPE_BY_KEY[tkey].emoji)
            if elite:
                cps = max(6, int(ts * 0.35))
                cp = emoji_pm("👑", cps)
                pp.drawPixmap(int(size / 2 - cps / 2), -int(ts * 0.05), cp)
            pp.end()
            self._fg_spr[key] = pm
        return pm

    def terrain_pixmap(self, b: Battle, ts: int) -> QPixmap:
        key = (b.map_id, ts)
        if self._tp_key == key: return self._tp
        pm = QPixmap(COLS * ts, ROWS * ts)
        pm.fill(QColor("#0e1116"))
        pp = QPainter(pm)
        f_base = emoji_font(ts); f_feat = emoji_font(int(ts * 0.82))
        for ix in range(COLS):
            col = b.terrain[ix]
            for iy in range(ROWS):
                tt = TERRAIN[col[iy]]
                r = QRectF(ix * ts - 0.5, iy * ts - 0.5, ts + 1, ts + 1)
                pp.setFont(f_base)
                pp.drawText(r, Qt.AlignmentFlag.AlignCenter, tt.base)
                if tt.feat:
                    pp.setFont(f_feat)
                    pp.drawText(r, Qt.AlignmentFlag.AlignCenter, tt.feat)
        pp.end()
        self._tp = pm; self._tp_key = key
        return pm

    def _unit_at(self, wx: float, wy: float) -> Optional[Unit]:
        best: Optional[Unit] = None
        bd = 0.36
        for u in self.win.battle.units:
            if u.alive:
                d2 = (u.x - wx) ** 2 + (u.y - wy) ** 2
                if d2 < bd: bd = d2; best = u
        return best

    def mouseMoveEvent(self, e: Any) -> None:
        win = self.win
        win.hover_unit = None
        if win.battle is not None and self._lay:
            ts, ox, oy = self._lay
            win.hover_unit = self._unit_at((e.position().x() - ox) / ts, (e.position().y() - oy) / ts)
        self.update()

    def mousePressEvent(self, e: Any) -> None:
        win = self.win
        if win.battle is not None and self._lay:
            ts, ox, oy = self._lay
            win.sel_unit = self._unit_at((e.position().x() - ox) / ts, (e.position().y() - oy) / ts)
        else:
            win.sel_unit = None
        self.win.brain.update()
        self.update()

    def leaveEvent(self, _: Any) -> None:
        self.win.hover_unit = None
        self.update()

    def paintEvent(self, _: Any) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.fillRect(self.rect(), QColor("#0e1116"))
        win = self.win
        b = win.battle
        if b is None:
            p.setFont(text_font(15)); p.setPen(QPen(QColor("#9aa4b2")))
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter,
                       "⚔️ Configure the armies on the right →\n\n"
                       "▶ Start to evolve generation 1  ·  🚀 to turbo-train\n\n"
                       "🧠 Click units to inspect brains  ·  🎁 toggle pickups\n"
                       "🗺️ Choose biome & preset  ·  📦 Batch Export multiple shorts")
            return

        W, H = self.width(), self.height()
        ts = max(8, int(min(W / COLS, H / ROWS)))
        
        # Dynamic Camera Shake
        if b.shake_t > 0:
            shake_factor = b.shake_t / 0.2
            sx_shake = int((random.random() - 0.5) * b.shake_mag * 16 * shake_factor)
            sy_shake = int((random.random() - 0.5) * b.shake_mag * 16 * shake_factor)
        else:
            sx_shake = 0
            sy_shake = 0
            
        ox = (W - ts * COLS) // 2 + sx_shake
        oy = (H - ts * ROWS) // 2 + sy_shake
        self._lay = (ts, ox, oy)

        p.drawPixmap(ox, oy, self.terrain_pixmap(b, ts))
        lite = b.lite

        if win.chk_debug.isChecked():
            p.save()
            for u in b.units:
                if not u.alive: continue
                c = QColor(TEAM_HEX[u.team]); c.setAlpha(110)
                p.setPen(QPen(c, 1))
                if u.target is not None and u.target.alive:
                    p.drawLine(QPointF(ox + u.x * ts, oy + u.y * ts),
                               QPointF(ox + u.target.x * ts, oy + u.target.y * ts))
                p.setPen(QPen(QColor(255, 255, 255, 130), 2))
                p.drawLine(QPointF(ox + u.x * ts, oy + u.y * ts),
                           QPointF(ox + (u.x + u.mvx * 1.2) * ts, oy + (u.y + u.mvy * 1.2) * ts))
            for u in b.units:
                if not u.alive: continue
                healer = (u.t.heal_power or 0) > 0
                if u.t.ranged or healer:
                    c = QColor("#57e389") if healer else QColor(TEAM_HEX[u.team])
                    c.setAlpha(60)
                    p.setPen(QPen(c, 1))
                    c2 = QColor(c); c2.setAlpha(16); p.setBrush(c2)
                    p.drawEllipse(QPointF(ox + u.x * ts, oy + u.y * ts), u.t.rng * ts, u.t.rng * ts)
            p.restore()

        pk_px = max(6, int(ts * 0.6))
        for i, pk in enumerate(b.pickups):
            bob = math.sin(b.time * 3 + i * 1.7) * 0.06 * ts
            p.drawPixmap(QPointF(ox + (pk[1] - 0.5) * ts, oy + (pk[2] - 0.5) * ts + bob), emoji_pm(pk[0], pk_px))

        pr_px = max(6, int(ts * 0.5))
        for pr in b.proj:
            px = ox + pr.x * ts; py = oy + pr.y * ts
            if pr.emoji:
                p.drawPixmap(QPointF(px - pr_px / 2, py - pr_px / 2), emoji_pm(pr.emoji, pr_px))
            else:
                c = QColor("#ffd93d") if pr.crit else TEAM_COLORS[pr.team]
                v = math.hypot(pr.vx, pr.vy) or 1.0
                p.setPen(QPen(c, 2))
                p.drawLine(QPointF(px - pr.vx / v * 6, py - pr.vy / v * 6), QPointF(px, py))
                p.setPen(Qt.PenStyle.NoPen); p.setBrush(c)
                p.drawEllipse(QPointF(px, py), 3, 3)

        # Combined Pass: Units, Health, and Fading
        for u in b.units:
            if not u.alive and u.fade_t <= 0: continue
            
            p.save()
            if not u.alive:
                p.setOpacity(u.fade_t / 0.4)
                
            cx = ox + u.x * ts; cy = oy + u.y * ts
            if u.lunge_t > 0:
                k = math.sin((1 - u.lunge_t / 0.16) * math.pi) * 0.3 * ts
                cx += u.lx * k; cy += u.ly * k
            bg = self.unit_bg_sprite(u.team, ts, u.elite)
            p.drawPixmap(QPointF(cx - bg.width() / 2, cy - bg.height() / 2), bg)

            fg = self.unit_fg_sprite(u.t.key, ts, u.elite)
            p.drawPixmap(QPointF(cx - fg.width() / 2, cy - fg.height() / 2), fg)

            if u is win.sel_unit:
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.setPen(QPen(QColor("#ffd93d"), 2))
                p.drawEllipse(QPointF(cx, cy), ts * 0.62, ts * 0.62)

            if u.alive:
                bw = ts * 0.92; bh = max(3, ts * 0.12)
                bx = cx - bw / 2; by = cy - ts * 0.70
                frac = clamp(u.disp_hp / u.max_hp, 0, 1)
                p.setBrush(QColor(15, 15, 15, 210)); p.setPen(Qt.PenStyle.NoPen)
                p.drawRect(QRectF(bx, by, bw, bh))
                p.setBrush(QColor(int(255 * (1 - frac)), int(60 + 150 * frac), 60))
                p.drawRect(QRectF(bx, by, bw * frac, bh))
                cdf = 1.0 - u.cd / u.t.cd
                if cdf < 1.0:
                    p.setBrush(QColor(80, 200, 255, 220))
                    p.drawRect(QRectF(bx, by + bh + 1, bw * cdf, max(2, bh * 0.6)))
                if u.flash > 0:
                    op = u.flash / 0.12 * 0.55
                    if not u.alive: op *= u.fade_t / 0.4
                    p.setOpacity(op)
                    p.setBrush(QColor(255, 255, 255))
                    p.setPen(Qt.PenStyle.NoPen)
                    p.drawEllipse(QPointF(cx, cy), ts * 0.5, ts * 0.5)
                if u.poison_t > 0 or u.buff_spd_t > 0 or u.buff_shd_t > 0:
                    bd_px = max(6, int(ts * 0.4))
                    if u.buff_spd_t > 0: p.drawPixmap(QPointF(cx - ts * 0.95, cy - ts * 0.95), emoji_pm("⚡", bd_px))
                    if u.buff_shd_t > 0: p.drawPixmap(QPointF(cx + ts * 0.45, cy - ts * 0.95), emoji_pm("🛡️", bd_px))
                    if u.poison_t > 0:   p.drawPixmap(QPointF(cx + ts * 0.18, cy - ts * 0.80), emoji_pm("☠️", bd_px))
            p.restore()

        # Particles (including new Rings)
        for pa in b.parts:
            if pa["kind"] == "ring":
                p.save()
                p.setOpacity(max(0.0, pa["ttl"] / pa["life"]))
                col = QColor(pa.get("col", "#add8e6")); col.setAlpha(150)
                p.setPen(QPen(col, 2))
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.drawEllipse(QPointF(ox + pa["x"] * ts, oy + pa["y"] * ts), pa["r"] * ts, pa["r"] * ts)
                p.restore()
                continue
            p.save()
            p.setOpacity(max(0.0, pa["ttl"] / pa["life"]))
            px = ox + pa["x"] * ts; py = oy + pa["y"] * ts
            if pa["kind"] == "emoji":
                sc = max(6, int(ts * pa.get("scale", 0.7)))
                p.drawPixmap(QPointF(px - sc / 2, py - sc / 2), emoji_pm(pa["ch"], sc))
            else:
                p.setFont(text_font(max(10, int(ts * pa.get("scale", 0.42)))))
                p.setPen(QPen(QColor(pa.get("col", "#ff6b6b"))))
                p.drawText(QPointF(px, py), pa["txt"])
            p.restore()

        if b.flash > 0:
            p.save()
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(255, 255, 240, int(b.flash / 0.25 * 80)))
            p.drawRect(self.rect())
            p.restore()

        hu = win.hover_unit
        if hu is not None and hu.alive:
            hx = ox + hu.x * ts; hy = oy + hu.y * ts
            lines = [f"{hu.t.emoji} {hu.t.name}{' 👑' if hu.elite else ''}   {'🟦' if hu.team == 0 else '🟥'}"]
            if hu.t.heal_power:
                lines.append(f"❤️ {hu.hp:.0f}/{hu.max_hp}   💚 heals {hu.t.heal_power}")
            else:
                lines.append(f"❤️ {hu.hp:.0f}/{hu.max_hp}   ⚔️ {hu.t.atk}   ✨{int(hu.t.crit*100)}%")
            lines.append(f"🏃 {hu.t.speed}   🎯 {hu.t.rng}" + ("   🕊️" if hu.fly else "") + ("   👻" if hu.phase else ""))
            lines.append(f"🗡️ {hu.fit_dmg:.0f}   ⚰️ {hu.fit_kills}   💚 {hu.fit_heal:.0f}   💰 {hu.fit_gold:.0f}")
            if hu.poison_t > 0:   lines.append("☠️ Poisoned!")
            if hu.buff_spd_t > 0: lines.append("⚡ Zooming!")
            if hu.buff_shd_t > 0: lines.append("🛡️ Shielded!")
            tw, th = 210, 18 * len(lines) + 10
            tx = clamp(hx + ts * 0.7, 4, W - tw - 4)
            ty = clamp(hy - ts * 0.5, 4, H - th - 4)
            p.setBrush(QColor(10, 12, 16, 235))
            p.setPen(QPen(QColor(TEAM_HEX[hu.team]), 1))
            p.drawRoundedRect(QRectF(tx, ty, tw, th), 5, 5)
            p.setPen(QPen(QColor("#e8edf2"))); p.setFont(text_font(12))
            for i2, ln in enumerate(lines):
                p.drawText(QPointF(tx + 8, ty + 18 + i2 * 18), ln)

        aA = b.aliveA; aB = b.aliveB
        mode = "  🚀" if win.state == "turbo" else ""
        nn_info = f" 🧠{b.nn_eval_time*1000:.1f}ms" if b else ""
        perf = f"   🖥️{win._fps:.0f} ⚙️{win._sps:.0f}/s{nn_info}" if win._sps > 0 else ""
        pk_info = f"  🎁{len(b.pickups)}" if b.pickups_on else ""
        rec_info = ""
        if win.exporter.recording:
            rec_info = f"  🔴BATCH {win.batch_current+1}/{win.batch_total} ({win.exporter.frame_count//win.exporter.fps}s)"
        p.fillRect(0, 0, W, 24, QColor(10, 12, 16, 195))
        p.setFont(text_font(14)); p.setPen(QPen(QColor("#e8edf2")))
        p.drawText(QRectF(8, 2, W - 16, 22), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                   f"🧬 Gen {win.gen}  ⏱ {b.time:4.1f}/{b.limit:.0f}s  🟦 {aA}/{b.nA}  🟥 {aB}/{b.nB}  "
                   f"🗺️{b.biome_name}{pk_info}{mode}{rec_info}{perf}")

        if b.over:
            p.fillRect(self.rect(), QColor(8, 10, 14, 150))
            if b.winner == 0:   msg, col = "🟦 BLUE TEAM WINS! 🏆", QColor("#6db3ff")
            elif b.winner == 1: msg, col = "🟥 RED TEAM WINS! 🏆", QColor("#ff7a7a")
            else:               msg, col = "🤝 DRAW!", QColor("#dddddd")
            p.setFont(text_font(30)); p.setPen(QPen(col))
            p.drawText(self.rect().adjusted(0, -40, 0, -40), Qt.AlignmentFlag.AlignCenter, msg)
            p.setFont(text_font(14)); p.setPen(QPen(QColor("#cfd8e3")))
            sub = ("Press ▶ Start for the next battle" if win.state == "idle" else "Evaluating fitness & breeding next generation…")
            p.drawText(self.rect().adjusted(0, 10, 0, 10), Qt.AlignmentFlag.AlignCenter, sub)

# ----------------------------- Main Window -----------------------------
class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.resize(1320, 820)

        self.ga = GAConfig()
        self.breeder = Breeder(self.ga)
        self.battle: Optional[Battle] = None
        self.state = "idle"
        self.gen = 1
        self.wins: dict[Optional[int], int] = {0: 0, 1: 0, None: 0}
        self.history: list[tuple[float, float]] = []
        self.banner_until = 0.0
        self.turbo_left = 0
        self.turbo_n = 0
        self.hover_unit: Optional[Unit] = None
        self.sel_unit: Optional[Unit] = None
        self.prev_best: dict[int, Optional[float]] = {0: None, 1: None}

        self.exporter = ShortsExporter()
        self.batch_total = 0
        self.batch_current = 0
        self.batch_prefix = ""
        self._batch_end_timer = float('inf')

        self._fps = 0.0
        self._sps = 0.0
        self._fps_n = 0
        self._step_n = 0
        self._meas_last = time.perf_counter()
        self._tframe = 0

        self._build_ui()
        QShortcut(QKeySequence(Qt.Key_Space), self, activated=self.on_start)
        QShortcut(QKeySequence(Qt.Key_N), self, activated=self.on_next)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(16)
        self.update_buttons()

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.addLayout(self._build_left_panel(), 1)
        root.addWidget(self._build_right_panel())

    def _build_left_panel(self) -> QVBoxLayout:
        left = QWidget()
        lv = QVBoxLayout(left)
        lv.setContentsMargins(0, 0, 0, 0)
        lv.setSpacing(4)
        self.board = BoardWidget(self)
        lv.addWidget(self.board, 1)
        self.brain = BrainWidget(self)
        lv.addWidget(self.brain)
        wrapper = QVBoxLayout()
        wrapper.addWidget(left)
        return wrapper

    def _build_right_panel(self) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFixedWidth(380)
        panel = QWidget()
        scroll.setWidget(panel)
        pv = QVBoxLayout(panel)
        pv.setSpacing(8)

        row = QHBoxLayout()
        self.btn_start = QPushButton("▶ Start")
        self.btn_next  = QPushButton("⏭ Next")
        self.btn_reset = QPushButton("♻ Reset")
        self.btn_start.clicked.connect(self.on_start)
        self.btn_next.clicked.connect(self.on_next)
        self.btn_reset.clicked.connect(self.on_reset)
        for w in (self.btn_start, self.btn_next, self.btn_reset): row.addWidget(w)
        pv.addLayout(row)

        pv.addWidget(self._build_armies_group())
        pv.addLayout(self._build_presets_row1())
        pv.addLayout(self._build_presets_row2())
        pv.addLayout(self._build_presets_row3())
        pv.addWidget(self._build_battle_group())
        pv.addWidget(self._build_shorts_group())
        pv.addWidget(self._build_evolution_group())
        pv.addWidget(self._build_status_group())
        pv.addStretch(1)

        self.log(f"🧮 NumPy brain acceleration: {'✅ ACTIVE' if _np is not None else '⚠️ not installed (pip install numpy)'}")
        self.log(f"📹 OpenCV video export: {'✅ AVAILABLE' if HAS_CV2 else '⚠️ not installed (pip install opencv-python)'}")
        self.log("🧬 Welcome! Battle → 📊 fitness → 🏆 breed. 🧠 Click units to watch brains.")
        self.log("🗺️ Choose biome & preset · 📦 Batch Export multiple shorts at once!")
        self.log("🚀 Perf: batched brains · spatial grid · sprite cache · throttled turbo.")
        return scroll

    def _build_armies_group(self) -> QGroupBox:
        gb = QGroupBox(f"🧬 Armies — {len(UNIT_TYPES)} unit types")
        g = QGridLayout(gb)
        h0, h1, h2 = QLabel("Unit"), QLabel("🟦"), QLabel("🟥")
        for h in (h1, h2): h.setAlignment(Qt.AlignmentFlag.AlignCenter)
        g.addWidget(h0, 0, 0); g.addWidget(h1, 0, 1); g.addWidget(h2, 0, 2)
        self.spins: dict[str, tuple[QSpinBox, QSpinBox]] = {}
        for i, t in enumerate(UNIT_TYPES, start=1):
            tips = [f"❤️ {t.hp} HP", f"⚔️ {t.atk or '—'} atk", f"🎯 {t.rng} range", f"🏃 {t.speed} speed",
                    f"⏱ {t.cd}s cd", f"✨ {int(t.crit*100)}% crit"]
            if t.armor < 1.0:    tips.append(f"🛡️ takes {int(t.armor*100)}% dmg")
            if t.lifesteal:      tips.append(f"🩸 lifesteal {int(t.lifesteal*100)}%")
            if t.fly:            tips.append("🕊️ flying — ignores terrain")
            if t.phase:          tips.append("👻 phases through obstacles")
            if t.poison:         tips.append(f"☠️ poison {t.poison[0]}/s · {t.poison[1]}s")
            if t.heal_power:     tips.append(f"💚 heals allies {t.heal_power}/hit")
            if t.revive:         tips.append("🌅 revives once at 50% HP")
            if t.lava_immune:    tips.append("🔥 immune to lava")
            if t.explode:        tips.append(f"💥 explodes on death ({t.explode[0]} dmg!)")
            tips.append(f"🧠 brain size: {t.hid}")
            lab = QLabel(f"{t.emoji} {t.name}")
            lab.setToolTip("   ·   ".join(tips))
            sa = QSpinBox(); sa.setRange(0, 12)
            sb = QSpinBox(); sb.setRange(0, 12)
            g.addWidget(lab, i, 0); g.addWidget(sa, i, 1); g.addWidget(sb, i, 2)
            self.spins[t.key] = (sa, sb)
        for (k, team), v in {("warrior", 0): 4, ("archer", 0): 2, ("zombie", 1): 5, ("alien", 1): 2}.items():
            self.spins[k][team].setValue(v)
        return gb

    def _build_presets_row1(self) -> QHBoxLayout:
        row = QHBoxLayout()
        for txt, fn in [("⚖️ 5v5", self.preset_duel), ("🏹 Ranged", self.preset_ranged),
                        ("🐝 Swarm", self.preset_swarm), ("🎲 Random", self.preset_random)]:
            b = QPushButton(txt); b.clicked.connect(fn); row.addWidget(b)
        return row

    def _build_presets_row2(self) -> QHBoxLayout:
        row = QHBoxLayout()
        for txt, fn in [("🦖 Boss", self.preset_boss), ("🧛 Undead", self.preset_undead),
                        ("🧚 Support", self.preset_support), ("🧹 Clear", self.preset_clear)]:
            b = QPushButton(txt); b.clicked.connect(fn); row.addWidget(b)
        return row

    def _build_presets_row3(self) -> QHBoxLayout:
        row = QHBoxLayout()
        for txt, fn in [("🦁 Beasts", self.preset_beasts), ("🎃 Bombs", self.preset_bombs)]:
            b = QPushButton(txt); b.clicked.connect(fn); row.addWidget(b)
        return row

    def _build_battle_group(self) -> QGroupBox:
        gb = QGroupBox("⚔️ Battle")
        f = QGridLayout(gb)
        f.addWidget(QLabel("⏱ Time limit (s)"), 0, 0)
        self.spin_limit = QSpinBox()
        self.spin_limit.setRange(10, 180)  # Max 180 seconds (3 minutes)
        self.spin_limit.setValue(60)
        f.addWidget(self.spin_limit, 0, 1)
        f.addWidget(QLabel("🎬 Sim speed"), 1, 0)
        self.sld_speed = QSlider(Qt.Orientation.Horizontal); self.sld_speed.setRange(1, 64); self.sld_speed.setValue(4)
        self.sld_speed.valueChanged.connect(self._speed_lbl)
        self.lbl_speed = QLabel("1.0×")
        f.addWidget(self.sld_speed, 1, 1); f.addWidget(self.lbl_speed, 1, 2)
        f.addWidget(QLabel("🚀 Turbo gens"), 2, 0)
        self.spin_turbo = QSpinBox(); self.spin_turbo.setRange(1, 200); self.spin_turbo.setValue(10)
        f.addWidget(self.spin_turbo, 2, 1)
        self.btn_turbo = QPushButton("🚀 Turbo-train")
        self.btn_turbo.clicked.connect(self.on_turbo)
        f.addWidget(self.btn_turbo, 2, 2)
        f.addWidget(QLabel("🗺️ Biome"), 3, 0)
        self.combo_biome = QComboBox()
        for key, biome in BIOMES.items():
            self.combo_biome.addItem(biome["name"], key)
        self.combo_biome.currentIndexChanged.connect(self._on_biome_changed)
        f.addWidget(self.combo_biome, 3, 1, 1, 2)
        f.addWidget(QLabel("📐 Preset"), 4, 0)
        self.combo_preset = QComboBox()
        for key, preset in LEVEL_PRESETS.items():
            self.combo_preset.addItem(preset["name"], key)
        self.combo_preset.currentIndexChanged.connect(self._on_preset_changed)
        f.addWidget(self.combo_preset, 4, 1, 1, 2)
        self.btn_map = QPushButton("🗺️ New map")
        self.btn_map.clicked.connect(self.on_newmap)
        f.addWidget(self.btn_map, 5, 0)
        self.chk_pickups = QCheckBox("🎁 Pickups 🧪💰⚡🛡️")
        self.chk_pickups.setChecked(True)
        self.chk_pickups.setToolTip("🎁 Loot spawns: 🧪 heal · 💰 fitness gold · ⚡ speed · 🛡️ shield.")
        f.addWidget(self.chk_pickups, 5, 1, 1, 2)
        f.addWidget(QLabel("📐 Formation"), 6, 0)
        self.combo_form = QComboBox(); self.combo_form.addItems(FORM_LABELS)
        f.addWidget(self.combo_form, 6, 1, 1, 2)
        self.chk_auto   = QCheckBox("🔁 Auto-start next battle"); self.chk_auto.setChecked(True)
        self.chk_newmap = QCheckBox("🗺️ New terrain each battle"); self.chk_newmap.setChecked(True)
        self.chk_debug  = QCheckBox("👁 Show targets, movement & ranges")
        self.chk_lite   = QCheckBox("🪶 Light FX at high speed (perf)"); self.chk_lite.setChecked(True)
        f.addWidget(self.chk_auto, 7, 0, 1, 3)
        f.addWidget(self.chk_newmap, 8, 0, 1, 3)
        f.addWidget(self.chk_debug, 9, 0, 1, 3)
        f.addWidget(self.chk_lite, 10, 0, 1, 3)
        return gb

    def _build_shorts_group(self) -> QGroupBox:
        gb = QGroupBox("📺 YouTube Shorts Batch")
        f = QGridLayout(gb)
        f.addWidget(QLabel("Number of Shorts"), 0, 0)
        self.spin_batch = QSpinBox()
        self.spin_batch.setRange(1, 100)
        self.spin_batch.setValue(5)
        f.addWidget(self.spin_batch, 0, 1)
        self.btn_batch = QPushButton("📦 Batch Export")
        self.btn_batch.clicked.connect(self.on_batch_export)
        f.addWidget(self.btn_batch, 1, 0, 1, 2)
        self.lbl_shorts = QLabel("📹 Ready · pip install opencv-python for export")
        self.lbl_shorts.setWordWrap(True)
        f.addWidget(self.lbl_shorts, 2, 0, 1, 2)
        return gb

    def _build_evolution_group(self) -> QGroupBox:
        gb = QGroupBox("🧠 Evolution (GA)")
        f = QGridLayout(gb)
        f.addWidget(QLabel("🎲 Mutation rate"), 0, 0)
        self.dsb_rate = QDoubleSpinBox(); self.dsb_rate.setRange(0.02, 0.8); self.dsb_rate.setSingleStep(0.01); self.dsb_rate.setValue(0.15)
        f.addWidget(self.dsb_rate, 0, 1)
        f.addWidget(QLabel("💪 Mutation strength"), 1, 0)
        self.dsb_str = QDoubleSpinBox(); self.dsb_str.setRange(0.05, 1.5); self.dsb_str.setSingleStep(0.05); self.dsb_str.setValue(0.35)
        f.addWidget(self.dsb_str, 1, 1)
        f.addWidget(QLabel("🔀 Crossover prob"), 2, 0)
        self.dsb_cross = QDoubleSpinBox(); self.dsb_cross.setRange(0.0, 1.0); self.dsb_cross.setSingleStep(0.05); self.dsb_cross.setValue(0.7)
        f.addWidget(self.dsb_cross, 2, 1)
        f.addWidget(QLabel("👑 Elites kept"), 3, 0)
        self.spin_elite = QSpinBox(); self.spin_elite.setRange(0, 3); self.spin_elite.setValue(1)
        f.addWidget(self.spin_elite, 3, 1)
        srow = QHBoxLayout()
        b_save = QPushButton("💾 Save"); b_save.clicked.connect(self.on_save)
        b_load = QPushButton("📂 Load"); b_load.clicked.connect(self.on_load)
        srow.addWidget(b_save); srow.addWidget(b_load)
        f.addLayout(srow, 4, 0, 1, 2)
        return gb

    def _build_status_group(self) -> QGroupBox:
        gb = QGroupBox("📊 Status")
        f = QGridLayout(gb)
        self.lbl_gen = QLabel("Generation: 1")
        self.lbl_wins = QLabel("🟦 0 · 🤝 0 · 0 🟥")
        f.addWidget(self.lbl_gen, 0, 0); f.addWidget(self.lbl_wins, 0, 1)
        self.lbl_champA = QLabel("🏅 🟦 champions: —")
        self.lbl_champR = QLabel("🏅 🟥 champions: —")
        f.addWidget(self.lbl_champA, 1, 0, 1, 2)
        f.addWidget(self.lbl_champR, 2, 0, 1, 2)
        ss = ("QProgressBar{border:1px solid #333c47;border-radius:4px;text-align:center;"
              "background:#0e1116;color:#dfe6ee;height:16px;} QProgressBar::chunk{border-radius:3px;}")
        self.barA = QProgressBar(); self.barA.setFormat("🟦 %v / %m")
        self.barA.setStyleSheet(ss + "QProgressBar::chunk{background:#3d8bfd;}")
        self.barB = QProgressBar(); self.barB.setFormat("🟥 %v / %m")
        self.barB.setStyleSheet(ss + "QProgressBar::chunk{background:#ff5c5c;}")
        f.addWidget(self.barA, 3, 0, 1, 2); f.addWidget(self.barB, 4, 0, 1, 2)
        self.graph = FitnessGraph(self)
        f.addWidget(self.graph, 5, 0, 1, 2)
        self.log_edit = QPlainTextEdit(); self.log_edit.setReadOnly(True)
        self.log_edit.setMinimumHeight(110)
        f.addWidget(self.log_edit, 6, 0, 1, 2)
        return gb

    def log(self, msg: str) -> None:
        self.log_edit.appendPlainText(msg)

    def _speed_lbl(self, v: int) -> None:
        self.lbl_speed.setText(f"{v / 4.0:.2f}×")

    def speed_value(self) -> float:
        return self.sld_speed.value() / 4.0

    def update_buttons(self) -> None:
        if self.state == "run": self.btn_start.setText("⏸ Pause")
        elif self.state == "pause": self.btn_start.setText("▶ Resume")
        elif self.state == "turbo": self.btn_start.setText("⏹ Stop turbo")
        elif self.state == "batch": self.btn_start.setText("⏹ Stop Batch")
        else: self.btn_start.setText("▶ Start")
        self.btn_next.setEnabled(self.state == "idle")

    def _on_biome_changed(self) -> None:
        self.breeder.biome_key = self.combo_biome.currentData()
        biome_name = BIOMES[self.breeder.biome_key]["name"]
        self.log(f"🗺️ Biome set to {biome_name}")

    def _on_preset_changed(self) -> None:
        self.breeder.preset_key = self.combo_preset.currentData()
        preset = LEVEL_PRESETS[self.breeder.preset_key]
        self.combo_biome.blockSignals(True)
        for i in range(self.combo_biome.count()):
            if self.combo_biome.itemData(i) == preset["biome"]:
                self.combo_biome.setCurrentIndex(i)
                self.breeder.biome_key = preset["biome"]
                break
        self.combo_biome.blockSignals(False)
        self.log(f"📐 Preset: {preset['name']} → {BIOMES[preset['biome']]['name']}")

    def read_counts(self) -> tuple[dict[tuple[int, str], int], int, int]:
        counts: dict[tuple[int, str], int] = {}
        nA = nB = 0
        for t in UNIT_TYPES:
            a = self.spins[t.key][0].value()
            b_ = self.spins[t.key][1].value()
            counts[(0, t.key)] = a
            counts[(1, t.key)] = b_
            nA += a; nB += b_
        return counts, nA, nB

    def update_champions(self) -> None:
        def line(team: int) -> str:
            hof = sorted(((v[1], k) for (t, k), v in self.breeder.hof.items() if t == team), reverse=True)
            medals = ["🥇", "🥈", "🥉"]
            return "  ".join(f"{medals[i]}{TYPE_BY_KEY[k].emoji}{fv:.0f}" for i, (fv, k) in enumerate(hof[:3])) or "—"
        self.lbl_champA.setText(f"🏅 🟦 champions: {line(0)}")
        self.lbl_champR.setText(f"🏅 🟥 champions: {line(1)}")

    def preset_clear(self) -> None:
        for sa, sb in self.spins.values(): sa.setValue(0); sb.setValue(0)

    def _set(self, key: str, a: int = 0, b: int = 0) -> None:
        if a: self.spins[key][0].setValue(a)
        if b: self.spins[key][1].setValue(b)

    def preset_duel(self) -> None:
        self.preset_clear(); self._set("warrior", a=5); self._set("zombie", b=5)

    def preset_ranged(self) -> None:
        self.preset_clear(); self._set("archer", a=6)
        self._set("alien", b=3); self._set("mage", b=3)

    def preset_swarm(self) -> None:
        self.preset_clear()
        self._set("bat", a=8); self._set("wasp", a=4)
        self._set("bear", b=3); self._set("guardian", b=2); self._set("fairy", b=1)

    def preset_boss(self) -> None:
        self.preset_clear()
        self._set("trex", a=1); self._set("fairy", a=1); self._set("guardian", a=2)
        self._set("zombie", b=6); self._set("archer", b=2)
        self._set("spider", b=2); self._set("pumpkin", b=1)

    def preset_undead(self) -> None:
        self.preset_clear()
        self._set("vampire", a=4); self._set("skeleton", a=6)
        self._set("fairy", b=2); self._set("guardian", b=3); self._set("elf", b=2)

    def preset_support(self) -> None:
        self.preset_clear()
        self._set("warrior", a=4); self._set("fairy", a=1)
        self._set("unicorn", a=1); self._set("archer", a=2)
        self._set("vampire", b=4); self._set("mage", b=2); self._set("guardian", b=2)

    def preset_beasts(self) -> None:
        self.preset_clear()
        self._set("lion", a=3); self._set("boar", a=3); self._set("wolf", a=2)
        self._set("skeleton", b=4); self._set("vampire", b=2); self._set("scorpion", b=2)

    def preset_bombs(self) -> None:
        self.preset_clear()
        self._set("pumpkin", a=4); self._set("guardian", a=2)
        self._set("zombie", b=3); self._set("mage", b=2); self._set("fairy", b=1)

    def preset_random(self) -> None:
        self.preset_clear()
        for sa, sb in self.spins.values():
            sa.setValue(random.randint(0, 4)); sb.setValue(random.randint(0, 4))
        if not any(x.value() for x in [s for p in self.spins.values() for s in p]):
            self._set("warrior", a=3); self._set("wolf", b=3)

    def start_battle(self, keep: bool = False) -> bool:
        counts, nA, nB = self.read_counts()
        if nA == 0 or nB == 0:
            self.log("⚠️ Both teams need at least one unit!")
            if not keep:
                self.state = "idle"; self.update_buttons()
            return False
        form = FORM_KEYS[self.combo_form.currentIndex()]
        pk_on = self.chk_pickups.isChecked()
        self.battle = Battle(counts, self.spin_limit.value(), self.breeder,
                             self.chk_newmap.isChecked(), form, pk_on)
        self.sel_unit = None
        if not keep:
            self.state = "run"; self.update_buttons()
        self.log(f"⚔️ Gen {self.gen}: {nA}🟦 vs {nB}🟥 · {self.spin_limit.value()}s · "
                 f"📐{FORM_LABELS[self.combo_form.currentIndex()]} · "
                 f"🗺️{self.battle.biome_name} · {self.battle.preset_name} · "
                 f"{'🎁 loot on' if pk_on else '🚫🎁 no loot'}")
        return True

    def finish_generation(self, immediate: bool = False) -> None:
        b = self.battle
        if not b: return
        self.ga.mut_rate = self.dsb_rate.value()
        self.ga.mut_strength = self.dsb_str.value()
        self.ga.crossover = self.dsb_cross.value()
        self.ga.elites = self.spin_elite.value()

        results = b.finalize()
        best = self.breeder.evolve(results, b.counts)

        def arrow(team: int, cur: float) -> str:
            prev = self.prev_best.get(team)
            self.prev_best[team] = cur
            if prev is None or prev <= 0: return ""
            pct = (cur - prev) / prev * 100
            if pct > 2:   return f" 📈+{pct:.0f}%"
            if pct < -2:  return f" 📉{pct:.0f}%"
            return " ➡️"

        def fmt(team: int) -> str:
            if team in best:
                k, fv = best[team]
                return f"{TYPE_BY_KEY[k].emoji}{fv:.0f}{arrow(team, fv)}"
            return "—"

        wt = {0: "🟦 wins! 🏆", 1: "🟥 wins! 🏆", None: "🤝 Draw!"}[b.winner]
        self.history.append((best.get(0, (None, 0.0))[1], best.get(1, (None, 0.0))[1]))
        if len(self.history) > 500: self.history.pop(0)

        self.log(f"🏁 Gen {self.gen}: {wt}  🟦 {fmt(0)} · 🟥 {fmt(1)}  (🧬 GA: {self.breeder.ga_time*1000:.1f}ms)")
        self.update_champions()
        self.gen += 1
        self.lbl_gen.setText(f"Generation: {self.gen}")
        self.graph.update()

        if immediate or self.chk_auto.isChecked():
            self.start_battle(keep=immediate)
        else:
            self.state = "idle"
            self.update_buttons()

    def refresh_status(self) -> None:
        b = self.battle
        if b:
            self.barA.setMaximum(max(1, b.init_hp[0]))
            self.barA.setValue(int(sum(u.hp for u in b.units if u.alive and u.team == 0)))
            self.barB.setMaximum(max(1, b.init_hp[1]))
            self.barB.setValue(int(sum(u.hp for u in b.units if u.alive and u.team == 1)))
        self.lbl_wins.setText(f"🟦 {self.wins[0]} · 🤝 {self.wins[None]} · {self.wins[1]} 🟥")

    def tick(self) -> None:
        self._fps_n += 1
        if self.battle is not None:
            self.battle.lite = self.chk_lite.isChecked() and (self.state == "turbo" or self.state == "batch" or self.speed_value() > 6)

        if self.state == "run" and self.battle and not self.battle.over:
            total = self.speed_value() * 0.016
            sub = max(1, min(16, math.ceil(total / 0.033)))
            dt = total / sub
            done = 0
            for _ in range(sub):
                self.battle.step(dt); done += 1
                if self.battle.over: break
            self._step_n += done
            if self.battle.over:
                self.state = "banner"
                self.banner_until = time.monotonic() + 1.6
                self.wins[self.battle.winner] += 1
                self.update_buttons()
            self.refresh_status()
            self.board.update()
            if self.sel_unit is not None: self.brain.update()

        elif self.state == "banner":
            self.board.update()
            if time.monotonic() >= self.banner_until: self.finish_generation()

        elif self.state == "batch" and self.battle:
            if not self.battle.over:
                total = self.speed_value() * 0.016
                sub = max(1, min(16, math.ceil(total / 0.033)))
                dt = total / sub
                done = 0
                for _ in range(sub):
                    self.battle.step(dt); done += 1
                    if self.battle.over: break
                self._step_n += done
                
                if self.battle.over:
                    self._batch_end_timer = time.monotonic() + 1.5
                    self.wins[self.battle.winner] += 1
            else:
                if time.monotonic() >= self._batch_end_timer:
                    self._finish_batch_video()
            
            self.refresh_status()
            self.board.update()
            if self.sel_unit is not None: self.brain.update()
            
            if self.exporter.recording:
                self.exporter.capture(self.board)
                if self.exporter.frame_count >= self.exporter.max_frames:
                    self._batch_end_timer = time.monotonic()

        elif self.state == "turbo":
            self._tframe += 1
            self.turbo_tick()
            self.refresh_status()
            if self._tframe % 3 == 0: self.board.update()
            if self._tframe % 8 == 0 and self.sel_unit is not None: self.brain.update()

        elif self.state == "pause":
            self.board.update()

        now = time.perf_counter()
        el = now - self._meas_last
        if el >= 0.5:
            self._fps = self._fps_n / el
            self._sps = self._step_n / el
            self._fps_n = 0; self._step_n = 0; self._meas_last = now

    def turbo_tick(self) -> None:
        end = time.perf_counter() + 0.045
        while time.perf_counter() < end:
            if self.battle is None or self.battle.over:
                if self.battle: self.wins[self.battle.winner] += 1
                self.finish_generation(immediate=True)
                self.turbo_left -= 1
                if self.turbo_left <= 0:
                    self.state = "idle"; self.update_buttons()
                    self.log(f"🚀 Turbo done — trained {self.turbo_n} generations! "
                             f"Record: 🟦{self.wins[0]} 🤝{self.wins[None]} {self.wins[1]}🟥")
                    return
                continue
            for _ in range(6):
                if self.battle.over: break
                self.battle.step(0.05)
                self._step_n += 1

    def on_start(self) -> None:
        if self.state == "batch":
            self.exporter.stop()
            self.state = "idle"
            self.battle = None
            self.update_buttons()
            self.log("⏹ Batch export cancelled.")
            self.lbl_shorts.setText("⏹ Batch cancelled")
            return

        if self.state == "run":
            self.state = "pause"; self.log("⏸ Paused")
        elif self.state == "turbo":
            self.state = "pause"; self.log("⏹ Turbo stopped — battle paused")
        elif self.state == "banner":
            self.finish_generation()
            if not self.chk_auto.isChecked(): self.start_battle()
        elif self.state == "pause" and self.battle and not self.battle.over:
            self.state = "run"; self.log("▶ Resumed")
        else:
            self.start_battle()
        self.update_buttons()

    def on_turbo(self) -> None:
        self.turbo_n = self.spin_turbo.value()
        self.turbo_left = self.turbo_n
        if self.state == "banner":
            if self.battle: self.wins[self.battle.winner] += 1
            self.finish_generation(immediate=True)
            self.turbo_left -= 1
        if self.battle is None:
            if not self.start_battle(keep=True): return
        self.state = "turbo"
        self.update_buttons()
        self.log(f"🚀 Turbo-training {self.turbo_n} generations at max speed…")

    def on_next(self) -> None:
        if self.state == "idle": self.start_battle()

    def on_newmap(self) -> None:
        if self.state != "idle": return
        self.breeder.terrain = None
        self.battle = None
        self.sel_unit = None
        self.board.update()
        self.brain.update()
        biome = self.combo_biome.currentData()
        preset = self.combo_preset.currentData()
        self.log(f"🗺️ Generated fresh {BIOMES[biome]['name']} — {LEVEL_PRESETS[preset]['name']}")

    def on_reset(self) -> None:
        self.breeder.reset()
        self.gen = 1
        self.wins = {0: 0, 1: 0, None: 0}
        self.history = []
        self.prev_best = {0: None, 1: None}
        self.battle = None
        self.sel_unit = None
        self.state = "idle"
        self.lbl_gen.setText("Generation: 1")
        self.update_champions()
        self.refresh_status()
        self.graph.update()
        self.update_buttons()
        self.board.update()
        self.brain.update()
        self.log("♻ Evolution wiped — genomes randomized, generation reset to 1.")

    def on_batch_export(self) -> None:
        if not HAS_CV2:
            self.log("⚠️ Cannot batch export: OpenCV not installed. Run: pip install opencv-python")
            return

        dir_path = QFileDialog.getExistingDirectory(self, "Select Folder to Save Shorts")
        if not dir_path:
            return

        self.batch_prefix = os.path.join(dir_path, "emoji_short_")
        self.batch_total = self.spin_batch.value()
        self.batch_current = 0
        
        counts, nA, nB = self.read_counts()
        if nA == 0 or nB == 0:
            self.log("⚠️ Need units for both teams to batch export!")
            return

        self.state = "batch"
        self.update_buttons()
        self._batch_end_timer = float('inf')
        self.start_batch_battle()

    def start_batch_battle(self) -> None:
        counts, nA, nB = self.read_counts()
        form = FORM_KEYS[self.combo_form.currentIndex()]
        pk_on = self.chk_pickups.isChecked()
        
        self.breeder.terrain = None
        self.battle = Battle(counts, self.spin_limit.value(), self.breeder,
                             True, form, pk_on)
        self.sel_unit = None
        self.log(f"📦 Batch {self.batch_current+1}/{self.batch_total}: Exporting...")
        
        path = f"{self.batch_prefix}{self.batch_current+1:03d}.mp4"
        if self.exporter.start(path):
            self.lbl_shorts.setText(f"🔴 Batch {self.batch_current+1}/{self.batch_total}...")
        else:
            self.log("⚠️ Failed to start recording.")
            self.state = "idle"; self.update_buttons()

    def _finish_batch_video(self) -> None:
        path, n = self.exporter.stop()
        self.log(f"📹 Saved short {self.batch_current+1}: {n} frames -> {path}")
        self.batch_current += 1
        
        if self.batch_current < self.batch_total:
            self.ga.mut_rate = self.dsb_rate.value()
            self.ga.mut_strength = self.dsb_str.value()
            self.ga.crossover = self.dsb_cross.value()
            self.ga.elites = self.spin_elite.value()
            
            results = self.battle.finalize()
            best = self.breeder.evolve(results, self.battle.counts)
            self.history.append((best.get(0, (None, 0.0))[1], best.get(1, (None, 0.0))[1]))
            if len(self.history) > 500: self.history.pop(0)
            self.gen += 1
            self.lbl_gen.setText(f"Generation: {self.gen}")
            self.update_champions()
            self.graph.update()
            
            self.start_batch_battle()
        else:
            self.log(f"✅ Batch export complete! {self.batch_total} shorts saved.")
            self.state = "idle"
            self.battle = None
            self.lbl_shorts.setText(f"✅ Exported {self.batch_total} shorts.")
            self.update_buttons()

    def on_save(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "💾 Save evolution", "evolution_save.json", "JSON (*.json)")
        if not path: return
        data = {
            "v": 42, "glen": GENOME_LEN, "gen": self.gen,
            "wins": {"blue": self.wins[0], "red": self.wins[1], "draw": self.wins[None]},
            "history": self.history,
            "ga": {"rate": self.dsb_rate.value(), "str": self.dsb_str.value(),
                   "cross": self.dsb_cross.value(), "elites": self.spin_elite.value()},
            "breeder": self.breeder.to_dict(),
            "biome": self.breeder.biome_key,
            "preset": self.breeder.preset_key,
        }
        try:
            with open(path, "w") as f: json.dump(data, f)
            self.log(f"💾 Saved evolution to {path}")
        except OSError as e:
            self.log(f"⚠️ Save failed: {e}")

    def on_load(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "📂 Load evolution", "", "JSON (*.json)")
        if not path: return
        try:
            with open(path) as f: data = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            self.log(f"⚠️ Load failed: {e}")
            return
        self.breeder.from_dict(data.get("breeder", {}))
        self.gen = data.get("gen", 1)
        w = data.get("wins", {})
        self.wins = {0: w.get("blue", 0), 1: w.get("red", 0), None: w.get("draw", 0)}
        self.history = [tuple(x) for x in data.get("history", [])]
        ga = data.get("ga", {})
        if ga:
            self.dsb_rate.setValue(ga.get("rate", 0.15))
            self.dsb_str.setValue(ga.get("str", 0.35))
            self.dsb_cross.setValue(ga.get("cross", 0.7))
            self.spin_elite.setValue(ga.get("elites", 1))
        bk = data.get("biome", "plains")
        pk = data.get("preset", "classic")
        if bk in BIOMES:
            self.breeder.biome_key = bk
            for i in range(self.combo_biome.count()):
                if self.combo_biome.itemData(i) == bk:
                    self.combo_biome.setCurrentIndex(i); break
        if pk in LEVEL_PRESETS:
            self.breeder.preset_key = pk
            for i in range(self.combo_preset.count()):
                if self.combo_preset.itemData(i) == pk:
                    self.combo_preset.setCurrentIndex(i); break
        self.battle = None
        self.sel_unit = None
        self.state = "idle"
        self.lbl_gen.setText(f"Generation: {self.gen}")
        self.update_champions()
        self.refresh_status()
        self.graph.update()
        self.update_buttons()
        self.board.update()
        self.brain.update()
        self.log(f"📂 Loaded evolution from {path} — resuming at gen {self.gen}.")

# ----------------------------- Entrypoint -----------------------------
def main() -> None:
    app = QApplication(sys.argv)
    app.setStyleSheet("""
        QWidget { background:#15181d; color:#dfe6ee; font-size:13px; }
        QGroupBox { border:1px solid #2a3038; border-radius:6px; margin-top:10px; font-weight:bold; }
        QGroupBox::title { subcontrol-origin:margin; left:8px; padding:0 4px; }
        QPushButton { background:#232a33; border:1px solid #333c47; border-radius:5px; padding:5px 8px; }
        QPushButton:hover { background:#2c3540; }
        QPushButton:disabled { color:#667; }
        QPlainTextEdit, QSpinBox, QDoubleSpinBox, QComboBox { background:#0e1116; border:1px solid #333c47; border-radius:3px; }
    """)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()