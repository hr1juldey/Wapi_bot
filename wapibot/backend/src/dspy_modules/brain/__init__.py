"""Brain DSPy modules for cognitive processing."""

from dspy_modules.brain.conflict_detector import ConflictDetector
from dspy_modules.brain.intent_predictor_module import IntentPredictor
from dspy_modules.brain.quality_evaluator import QualityEvaluator
from dspy_modules.brain.goal_decomposer_module import GoalDecomposer
from dspy_modules.brain.response_generator import ResponseGenerator

__all__ = [
    "ConflictDetector",
    "IntentPredictor",
    "QualityEvaluator",
    "GoalDecomposer",
    "ResponseGenerator",
]
