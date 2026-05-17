"""Derived gamification snapshot computed from the journal.

We never trust the `xp_event` table alone for totals — the source of truth
is the journal (`module_visit`, `exercise_attempt`, `quiz_answer`). The
events table is used for **idempotent** ledger writes (one `module_visit`
event per module) and for the "you just earned +25 XP" toast in the UI.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import (
    AchievementUnlock,
    Exercise,
    ExerciseAttempt,
    Module,
    ModuleVisit,
    QuizAnswer,
    XpEvent,
)
from ..services import gamification as gam


# === LOW-LEVEL WRITES ======================================================

async def _idempotent_xp(
    session: AsyncSession,
    *,
    user_id: int,
    event_type: str,
    ref_kind: str,
    ref_id: int,
    track: str | None = None,
) -> int:
    """Insert an XpEvent if (user, type, ref) is new. Returns points awarded
    (0 if it was already recorded)."""
    existing = await session.execute(
        select(XpEvent.id).where(
            XpEvent.user_id == user_id,
            XpEvent.event_type == event_type,
            XpEvent.ref_kind == ref_kind,
            XpEvent.ref_id == ref_id,
        )
    )
    if existing.scalar_one_or_none() is not None:
        return 0
    pts = gam.points_for(event_type, track=track)
    session.add(XpEvent(
        user_id=user_id,
        event_type=event_type,
        points=pts,
        ref_kind=ref_kind,
        ref_id=ref_id,
    ))
    await session.commit()
    return pts


async def record_module_visit_xp(
    session: AsyncSession, *, user_id: int, module: Module
) -> int:
    return await _idempotent_xp(
        session,
        user_id=user_id,
        event_type="module_visit",
        ref_kind="module",
        ref_id=module.id,
        track=module.track,
    )


async def record_exercise_passed_xp(
    session: AsyncSession, *, user_id: int, exercise_id: int
) -> int:
    """First time this exercise is passed; multiplied if it belongs to T0."""
    ex = await session.get(Exercise, exercise_id)
    track = None
    if ex is not None:
        mod = await session.get(Module, ex.module_id)
        track = mod.track if mod else None
    return await _idempotent_xp(
        session,
        user_id=user_id,
        event_type="exercise_passed",
        ref_kind="exercise",
        ref_id=exercise_id,
        track=track,
    )


async def record_quiz_correct_xp(
    session: AsyncSession, *, user_id: int, quiz_id: int
) -> int:
    return await _idempotent_xp(
        session,
        user_id=user_id,
        event_type="quiz_correct",
        ref_kind="quiz",
        ref_id=quiz_id,
    )


async def record_checkpoint_xp(
    session: AsyncSession,
    *,
    user_id: int,
    module_id: int,
    checkpoint_id: str,
    track: str | None = None,
) -> int:
    """Award XP once per (user, module, checkpoint_id).

    Uses a stable integer ref_id derived from module_id and the checkpoint
    string so the existing unique constraint covers it without schema change.
    The composite ref uses module_id as ref_id and stores checkpoint_id as
    part of event_type discriminator via ref_kind.
    """
    return await _idempotent_xp(
        session,
        user_id=user_id,
        event_type="checkpoint_reached",
        ref_kind=f"cp:{checkpoint_id}",
        ref_id=module_id,
        track=track,
    )


async def unlock(session: AsyncSession, *, user_id: int, code: str) -> bool:
    """Insert AchievementUnlock if not already present. Returns True if new."""
    existing = await session.execute(
        select(AchievementUnlock.id).where(
            AchievementUnlock.user_id == user_id,
            AchievementUnlock.code == code,
        )
    )
    if existing.scalar_one_or_none() is not None:
        return False
    session.add(AchievementUnlock(user_id=user_id, code=code))
    await session.commit()
    return True


# === READ: SNAPSHOT ========================================================

async def _xp_total(session: AsyncSession, user_id: int) -> int:
    q = select(func.coalesce(func.sum(XpEvent.points), 0)).where(
        XpEvent.user_id == user_id
    )
    return (await session.execute(q)).scalar_one() or 0


async def _active_days(session: AsyncSession, user_id: int) -> set:
    """Distinct calendar (UTC) days the user has done *anything*."""
    days = set()
    for table_col in (
        select(ModuleVisit.last_seen).where(ModuleVisit.user_id == user_id),
        select(ExerciseAttempt.created_at).where(ExerciseAttempt.user_id == user_id),
        select(QuizAnswer.created_at).where(QuizAnswer.user_id == user_id),
    ):
        res = await session.execute(table_col)
        for (dt,) in res.all():
            if dt is None:
                continue
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            days.add(dt.astimezone(timezone.utc).date())
    return days


async def _max_combo_no_solution(session: AsyncSession, user_id: int) -> int:
    """Longest streak of `passed=True` attempts in time order.

    We don't currently track "saw the solution" explicitly, so this is a
    proxy: pure passes in a row. Showing the solution doesn't generate an
    attempt row, so the streak survives. If the next attempt fails, the
    streak resets.
    """
    res = await session.execute(
        select(ExerciseAttempt.passed)
        .where(ExerciseAttempt.user_id == user_id)
        .order_by(ExerciseAttempt.created_at.asc())
    )
    cur = best = 0
    for (passed,) in res.all():
        if passed:
            cur += 1
            best = max(best, cur)
        else:
            cur = 0
    return best


async def _track_completion(session: AsyncSession, user_id: int) -> dict[str, bool]:
    """A track is 'complete' when every module in it has at least one visit."""
    by_track: dict[str, set[int]] = defaultdict(set)
    visited_by_track: dict[str, set[int]] = defaultdict(set)
    mods = (await session.execute(select(Module.id, Module.track))).all()
    for mid, t in mods:
        by_track[t].add(mid)
    visits = (await session.execute(
        select(ModuleVisit.module_id, Module.track)
        .join(Module, Module.id == ModuleVisit.module_id)
        .where(ModuleVisit.user_id == user_id)
    )).all()
    for mid, t in visits:
        visited_by_track[t].add(mid)
    return {
        t: bool(by_track[t]) and visited_by_track[t] >= by_track[t]
        for t in by_track
    }


async def _hello_world_done(session: AsyncSession, user_id: int) -> bool:
    """Any passed attempt against the very first Track 0 exercise (ord=1
    inside the first module of track '0'). Tolerant if T0 doesn't exist yet.
    """
    res = await session.execute(
        select(Module).where(Module.track == "0").order_by(Module.ord).limit(1)
    )
    first_t0 = res.scalar_one_or_none()
    if first_t0 is None:
        return False
    res = await session.execute(
        select(func.count())
        .select_from(ExerciseAttempt)
        .join(Exercise, Exercise.id == ExerciseAttempt.exercise_id)
        .where(
            ExerciseAttempt.user_id == user_id,
            ExerciseAttempt.passed.is_(True),
            Exercise.module_id == first_t0.id,
        )
    )
    return (res.scalar_one() or 0) >= 1


async def _first_conditional_done(session: AsyncSession, user_id: int) -> bool:
    """Heuristic: a passed attempt whose code contains an `if`. Track 0 has
    a dedicated "primer if/else" module; this catches it without binding to
    a specific slug."""
    res = await session.execute(
        select(ExerciseAttempt.code)
        .where(
            ExerciseAttempt.user_id == user_id,
            ExerciseAttempt.passed.is_(True),
        )
    )
    for (code,) in res.all():
        if code and "if " in code:
            return True
    return False


async def _capstone_done(session: AsyncSession, user_id: int) -> bool:
    res = await session.execute(
        select(Module).where(Module.ext_id == "E06").limit(1)
    )
    cap = res.scalar_one_or_none()
    if cap is None:
        return False
    res = await session.execute(
        select(ModuleVisit).where(
            ModuleVisit.user_id == user_id,
            ModuleVisit.module_id == cap.id,
        )
    )
    visit = res.scalar_one_or_none()
    if visit is None:
        return False
    # capstone "ready" = visited AND at least one passed exercise in it.
    res = await session.execute(
        select(func.count())
        .select_from(ExerciseAttempt)
        .join(Exercise, Exercise.id == ExerciseAttempt.exercise_id)
        .where(
            ExerciseAttempt.user_id == user_id,
            ExerciseAttempt.passed.is_(True),
            Exercise.module_id == cap.id,
        )
    )
    return (res.scalar_one() or 0) >= 1


async def _visited_module_ids(session: AsyncSession, user_id: int) -> set[int]:
    res = await session.execute(
        select(ModuleVisit.module_id).where(ModuleVisit.user_id == user_id)
    )
    return {row[0] for row in res.all()}


async def _passed_exercise_count(session: AsyncSession, user_id: int) -> int:
    res = await session.execute(
        select(func.count(func.distinct(ExerciseAttempt.exercise_id))).where(
            ExerciseAttempt.user_id == user_id,
            ExerciseAttempt.passed.is_(True),
        )
    )
    return res.scalar_one() or 0


async def _correct_quiz_count(session: AsyncSession, user_id: int) -> int:
    res = await session.execute(
        select(func.count(func.distinct(QuizAnswer.quiz_id))).where(
            QuizAnswer.user_id == user_id,
            QuizAnswer.correct.is_(True),
        )
    )
    return res.scalar_one() or 0


async def _existing_unlocks(session: AsyncSession, user_id: int) -> set[str]:
    res = await session.execute(
        select(AchievementUnlock.code).where(AchievementUnlock.user_id == user_id)
    )
    return {r[0] for r in res.all()}


def _streak_prompt(streak_days: int, active_days: set[date]) -> str | None:
    """Return a retention nudge string or None.

    - streak_days == 1: encourage return tomorrow.
    - streak is currently 0 (cold) but user had a streak > 1 within last 7 days:
      show "racha viva" prompt with the peak streak length.
    """
    if streak_days == 1:
        return "vuelve mañana para 2 días al hilo"
    if streak_days == 0 and active_days:
        today = datetime.now(timezone.utc).date()
        window_start = today - timedelta(days=7)
        # find the longest streak that includes any day in the last 7 days
        recent_days = {d for d in active_days if window_start <= d < today}
        if not recent_days:
            return None
        # reconstruct peak streak length for each day in recent window
        peak = 0
        for d in recent_days:
            length = 0
            cur = d
            while cur in active_days:
                length += 1
                cur -= timedelta(days=1)
            if length > peak:
                peak = length
        if peak > 1:
            return f"tu racha de {peak} días sigue viva si vuelves hoy"
    return None


async def per_track_progress(
    session: AsyncSession, *, user_id: int
) -> dict[str, dict]:
    """For sidebar / home: per-track counts of visited vs total modules."""
    mods = (await session.execute(
        select(Module.id, Module.track).order_by(Module.ord)
    )).all()
    visited = await _visited_module_ids(session, user_id)
    out: dict[str, dict] = {}
    for mid, t in mods:
        e = out.setdefault(t, {"total": 0, "visited": 0})
        e["total"] += 1
        if mid in visited:
            e["visited"] += 1
    for t, e in out.items():
        e["pct"] = int(round(100 * e["visited"] / e["total"])) if e["total"] else 0
    return out


async def next_module(
    session: AsyncSession, *, user_id: int, current_module_id: int | None = None
) -> Module | None:
    """The smallest-`ord` unvisited module, optionally biased to be 'after'
    `current_module_id`. Used for the "siguiente módulo" CTA card.
    """
    visited = await _visited_module_ids(session, user_id)
    mods = list((await session.execute(
        select(Module).order_by(Module.ord)
    )).scalars().all())
    if not mods:
        return None
    if current_module_id is not None:
        try:
            idx = next(i for i, m in enumerate(mods) if m.id == current_module_id)
        except StopIteration:
            idx = -1
        # prefer the next-in-list module (visited or not), as a clear CTA.
        if 0 <= idx < len(mods) - 1:
            return mods[idx + 1]
    for m in mods:
        if m.id not in visited:
            return m
    return mods[0]


async def snapshot(session: AsyncSession, *, user_id: int) -> dict:
    """One-shot computation of everything the UI needs.

    Returns a dict (not a dataclass) so Jinja templates can consume it
    directly without import gymnastics.
    """
    xp = await _xp_total(session, user_id)
    cur_lvl, nxt_lvl, xp_into, xp_for_next = gam.level_for_xp(xp)
    days = await _active_days(session, user_id)
    streak = gam.streak_from_days(days)
    track_done = await _track_completion(session, user_id)

    # Hoist counters so eval_unlocks and near_unlocks share them.
    visited_ids = await _visited_module_ids(session, user_id)
    passed_count = await _passed_exercise_count(session, user_id)
    quiz_count = await _correct_quiz_count(session, user_id)
    combo = await _max_combo_no_solution(session, user_id)
    cap_done = await _capstone_done(session, user_id)
    hw_done = await _hello_world_done(session, user_id)
    cond_done = await _first_conditional_done(session, user_id)

    earned = gam.eval_unlocks(
        visited_module_ids=visited_ids,
        passed_exercise_count=passed_count,
        correct_quiz_count=quiz_count,
        max_combo_no_solution=combo,
        track_completion=track_done,
        streak_days=streak,
        capstone_done=cap_done,
        hello_world_done=hw_done,
        first_conditional_done=cond_done,
    )
    persisted = await _existing_unlocks(session, user_id)
    newly = earned - persisted
    for code in newly:
        await unlock(session, user_id=user_id, code=code)

    pct_to_next = (
        int(round(100 * xp_into / xp_for_next)) if xp_for_next else 100
    )

    # === near_unlocks: ≥50% progress, not yet earned, top-3 closest =========
    def _near_unlocks_list() -> list[dict]:
        candidates: list[dict] = []

        def _add(code: str, progress: int, target: int, missing_label: str) -> None:
            if code in earned:
                return
            pct = progress / target if target else 0
            if pct >= 0.5:
                a = gam.ACHIEVEMENTS_BY_CODE.get(code)
                if a:
                    candidates.append({
                        "code": code,
                        "name": a.title,
                        "progress": progress,
                        "target": target,
                        "missing_label": missing_label,
                        "_pct": pct,
                    })

        # combo_3 / combo_5
        _add("combo_3", combo, 3,
             f"te falt{'a' if (3 - combo) == 1 else 'an'} {3 - combo} ejercicio{'s' if (3 - combo) != 1 else ''} al hilo para `combo_3`")
        _add("combo_5", combo, 5,
             f"te falt{'a' if (5 - combo) == 1 else 'an'} {5 - combo} ejercicio{'s' if (5 - combo) != 1 else ''} al hilo para `combo_5`")
        # ten_modules
        _add("ten_modules", len(visited_ids), 10,
             f"te falt{'a' if (10 - len(visited_ids)) == 1 else 'an'} {10 - len(visited_ids)} módulo{'s' if (10 - len(visited_ids)) != 1 else ''} para `ten_modules`")
        # streak_3_days / streak_7_days
        _add("streak_3_days", streak, 3,
             f"te falt{'a' if (3 - streak) == 1 else 'an'} {3 - streak} día{'s' if (3 - streak) != 1 else ''} consecutivo{'s' if (3 - streak) != 1 else ''} para `streak_3_days`")
        _add("streak_7_days", streak, 7,
             f"te falt{'a' if (7 - streak) == 1 else 'an'} {7 - streak} día{'s' if (7 - streak) != 1 else ''} consecutivo{'s' if (7 - streak) != 1 else ''} para `streak_7_days`")
        # first_quiz
        _add("first_quiz", quiz_count, 1,
             "responde un quiz para `first_quiz`")
        # hello_world
        _add("hello_world", 1 if hw_done else 0, 1,
             "ejecuta tu primer print() para `hello_world`")
        # first_if
        _add("first_if", 1 if cond_done else 0, 1,
             "pasa un ejercicio con if para `first_if`")

        candidates.sort(key=lambda c: c["_pct"], reverse=True)
        for c in candidates:
            del c["_pct"]
        return candidates[:3]

    near = _near_unlocks_list()

    achievements_catalog = [
        {
            "code": a.code,
            "title": a.title,
            "description": a.description,
            "icon": a.icon,
            "unlocked": a.code in earned,
        }
        for a in gam.ACHIEVEMENTS
    ]

    return {
        "xp": xp,
        "level": {
            "idx": cur_lvl.idx,
            "name": cur_lvl.name,
            "blurb": cur_lvl.blurb,
            "threshold": cur_lvl.threshold,
        },
        "next_level": (
            {"idx": nxt_lvl.idx, "name": nxt_lvl.name, "threshold": nxt_lvl.threshold}
            if nxt_lvl else None
        ),
        "xp_into_level": xp_into,
        "xp_for_next_level": xp_for_next,
        "pct_to_next_level": pct_to_next,
        "streak_days": streak,
        "streak_prompt": _streak_prompt(streak, days),
        "achievements_earned": sorted(earned),
        "achievements_total": len(gam.ACHIEVEMENTS),
        "achievements_catalog": achievements_catalog,
        "achievements_all": achievements_catalog,
        "achievements_unlocked": sorted(earned),
        "newly_unlocked": sorted(newly),
        "track_completion": track_done,
        "near_unlocks": near,
    }
