"""Gamification catalog: XP events, levels, achievements.

This is pure data + pure functions. No DB writes here. The repo
(`app.repos.gamification`) is the one that turns the journal of
`ExerciseAttempt`/`QuizAnswer`/`ModuleVisit` rows into a derived snapshot
(XP total, level, streak, unlocked achievements).

Why pure: the rules can be re-applied to existing history if the catalog
changes. We never lose engagement signal because the journal is the truth.

Note on Track 0 ("Cimientos"): the audience is non-programmers whose only
computational reference is Excel formulas. Track 0 modules get an
*onboarding multiplier* so the XP bar moves visibly in the first session
(first 30-60 minutes). Wins must arrive every 2-3 minutes there.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone


# === XP CATALOG ============================================================

@dataclass(frozen=True)
class XpRule:
    event_type: str
    points: int
    label: str  # human-readable, Spanish

XP_RULES: list[XpRule] = [
    XpRule("module_visit",         10, "Abrir un módulo por primera vez"),
    XpRule("exercise_attempted",    3, "Intentar un ejercicio aunque falle"),
    XpRule("exercise_passed",      25, "Pasar un ejercicio (sin ver solución)"),
    XpRule("quiz_correct",          5, "Acertar un quiz"),
    XpRule("streak_combo_3",       50, "3 ejercicios pasados al hilo"),
    XpRule("track_completed",     200, "Completar un track entero"),
    XpRule("daily_login",           5, "Volver hoy"),
    XpRule("checkpoint_reached",    5, "Leer una sección completa del módulo"),
]

XP_BY_TYPE: dict[str, int] = {r.event_type: r.points for r in XP_RULES}

# Track 0 ("Cimientos") is the entry track for non-programmers coming from
# Excel. We multiply rewards so first-session engagement is high: the bar
# visibly moves with copy-pasting a `print("hola")` and reading two modules.
TRACK_0_MULTIPLIER = 2

def points_for(event_type: str, *, track: str | None = None) -> int:
    base = XP_BY_TYPE.get(event_type, 0)
    if track == "0":
        return base * TRACK_0_MULTIPLIER
    return base


# === LEVELS ================================================================

@dataclass(frozen=True)
class Level:
    idx: int
    name: str
    threshold: int  # cumulative XP required to enter this level
    blurb: str

# Thresholds calibrated so a first Track-0 session (open 3 modules, pass
# 4 easy exercises, hit one quiz) breaks Aprendiz -> Practicante.
# 3*20 + 4*50 + 1*10 = 270 -> well past Practicante's 150.
LEVELS: list[Level] = [
    Level(1, "Aprendiz",     0,    "Acabas de abrir el libro."),
    Level(2, "Practicante",  150,  "Ya escribes código sin copiar y pegar."),
    Level(3, "Ingeniero",    500,  "Resuelves problemas, no solo ejercicios."),
    Level(4, "Arquitecto",   1200, "Decides cuándo NO usar un agente."),
    Level(5, "Hero",         2500, "Capaz de vender lo que construyes."),
]


def level_for_xp(xp: int) -> tuple[Level, "Level | None", int, int]:
    """Return (current_level, next_level_or_None, xp_into_level, xp_for_next).

    `xp_for_next` is the *span* of the current level (delta XP between
    its threshold and the next level's threshold). `xp_into_level` is how
    much XP has been earned since entering the current level.
    """
    current = LEVELS[0]
    for lvl in LEVELS:
        if xp >= lvl.threshold:
            current = lvl
        else:
            break
    nxt_idx = current.idx
    nxt: Level | None = LEVELS[nxt_idx] if nxt_idx < len(LEVELS) else None
    xp_into = xp - current.threshold
    xp_for_next = (nxt.threshold - current.threshold) if nxt else 0
    return current, nxt, xp_into, xp_for_next


# === ACHIEVEMENTS ==========================================================

@dataclass(frozen=True)
class Achievement:
    code: str
    title: str            # short Spanish title
    description: str      # one line
    icon: str             # short ascii/unicode glyph

ACHIEVEMENTS: list[Achievement] = [
    # Track 0 onboarding — must trigger in the first session
    Achievement("hello_world",     "Hola, mundo",          "Ejecutaste tu primer `print(\"hola\")`.",       "hi"),
    Achievement("left_excel",      "Saliste de Excel",     "Abriste tu primer módulo de programación.",     "ex"),
    Achievement("first_if",        "Primer if/else",       "Pasaste un ejercicio con condicional.",         "if"),
    # Core
    Achievement("first_quiz",      "Primera respuesta",    "Acertaste tu primer quiz.",                     "q"),
    Achievement("combo_3",         "Tres seguidos",        "3 ejercicios pasados al hilo sin ver solución.","3x"),
    Achievement("combo_5",         "Cinco al hilo",        "5 ejercicios pasados al hilo sin ver solución.","5x"),
    # Track milestones
    Achievement("track_0",         "Cimientos listos",     "Completaste el Track 0 (Cimientos).",           "T0"),
    Achievement("track_a",         "Python pragmático",    "Completaste el Track A.",                       "TA"),
    Achievement("track_e",         "Primer agente",        "Completaste el Track E (agentes IA).",          "TE"),
    # Volume & habit
    Achievement("ten_modules",     "Diez módulos",         "Visitaste 10 módulos distintos.",               "10"),
    Achievement("streak_3_days",   "Tres días seguidos",   "Tres días consecutivos de uso.",                "3d"),
    Achievement("streak_7_days",   "Una semana entera",    "Siete días consecutivos de uso.",               "7d"),
    Achievement("capstone_ready",  "Capstone listo",       "Completaste el módulo capstone (E06).",         "E6"),
]

ACHIEVEMENTS_BY_CODE: dict[str, Achievement] = {a.code: a for a in ACHIEVEMENTS}


# === STREAK ================================================================

def streak_from_days(active_days: set[date], today: date | None = None) -> int:
    """Compute current consecutive-day streak ending today or yesterday.

    We accept *yesterday* as the anchor too: the user may not have opened
    the app yet today. The streak only breaks once we miss a full day.
    """
    if today is None:
        today = datetime.now(timezone.utc).date()
    anchor = today if today in active_days else (today - timedelta(days=1))
    if anchor not in active_days:
        return 0
    streak = 0
    d = anchor
    while d in active_days:
        streak += 1
        d -= timedelta(days=1)
    return streak


# === ACHIEVEMENT EVALUATION ===============================================

def eval_unlocks(
    *,
    visited_module_ids: set[int],
    passed_exercise_count: int,
    correct_quiz_count: int,
    max_combo_no_solution: int,
    track_completion: dict[str, bool],
    streak_days: int,
    capstone_done: bool,
    hello_world_done: bool,
    first_conditional_done: bool,
) -> set[str]:
    """Return the set of achievement codes the user has earned right now.

    Pure function over derived counters; the repo computes the counters
    from the journal.
    """
    unlocks: set[str] = set()
    if len(visited_module_ids) >= 1:
        unlocks.add("left_excel")
    if hello_world_done:
        unlocks.add("hello_world")
    if first_conditional_done:
        unlocks.add("first_if")
    if correct_quiz_count >= 1:
        unlocks.add("first_quiz")
    if max_combo_no_solution >= 3:
        unlocks.add("combo_3")
    if max_combo_no_solution >= 5:
        unlocks.add("combo_5")
    if track_completion.get("0"):
        unlocks.add("track_0")
    if track_completion.get("A"):
        unlocks.add("track_a")
    if track_completion.get("E"):
        unlocks.add("track_e")
    if len(visited_module_ids) >= 10:
        unlocks.add("ten_modules")
    if streak_days >= 3:
        unlocks.add("streak_3_days")
    if streak_days >= 7:
        unlocks.add("streak_7_days")
    if capstone_done:
        unlocks.add("capstone_ready")
    return unlocks
