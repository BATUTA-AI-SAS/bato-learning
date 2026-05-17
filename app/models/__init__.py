"""ORM models. Imported eagerly so Alembic autogenerate sees them."""
from .chat import ChatMessage, ChatSession  # noqa: F401
from .content import Exercise, Module, Quiz, QuizOption  # noqa: F401
from .game import (  # noqa: F401
    Chapter,
    Decision,
    DecisionChoice,
    GameLevel,
    LoreDrop,
    LoreUnlock,
    LevelAttempt,
    Recipe,
    SkillMastery,
    UserProgress,
)
from .gamification import AchievementUnlock, XpEvent  # noqa: F401
from .progress import ExerciseAttempt, ModuleVisit, QuizAnswer  # noqa: F401
from .user import User  # noqa: F401
