"""Celery task for GEPA optimizer - reflective prompt evolution."""

import logging
import dspy
from tasks import celery_app
from repositories.brain_decision_repo import BrainDecisionRepository
from core.brain_config import get_brain_settings
from core.dspy_config import dspy_configurator
from services.dataset_builder import DatasetBuilder
from dspy_modules.brain import (
    ConflictDetector,
    IntentPredictor,
    QualityEvaluator,
    GoalDecomposer,
    ResponseGenerator
)
from dspy_modules.metrics import (
    conflict_metric,
    intent_metric,
    quality_metric,
    goals_metric,
    response_metric
)
from dspy_modules.module_loader import save_optimized_modules

logger = logging.getLogger(__name__)


@celery_app.task(name="brain.gepa_optimize")
def run_gepa_optimization(num_iterations: int = 100) -> dict:
    """Execute GEPA optimization on brain decisions.

    Applies reflective prompt evolution to improve brain modules.

    Args:
        num_iterations: Number of optimization iterations

    Returns:
        Dict with optimization results
    """
    try:
        settings = get_brain_settings()

        if not settings.rl_gym_enabled:
            logger.info("⏭️ RL Gym disabled in config")
            return {"status": "skipped", "reason": "disabled"}

        # Get recent decisions
        decision_repo = BrainDecisionRepository()
        decisions = decision_repo.get_recent(num_iterations)

        if len(decisions) < num_iterations:
            logger.info(f"⏳ Not enough decisions: {len(decisions)}/{num_iterations}")
            return {"status": "skipped", "reason": "insufficient_data"}

        # Build datasets for all modules
        logger.info(f"🧠 GEPA optimization: {len(decisions)} decisions")

        builder = DatasetBuilder(decision_repo)
        datasets = builder.build_all_datasets(num_decisions=len(decisions))

        # Student LLM already configured via dspy_configurator.configure()
        # Initialize baseline modules
        baseline_modules = {
            "conflict": ConflictDetector(),
            "intent": IntentPredictor(),
            "quality": QualityEvaluator(),
            "goals": GoalDecomposer(),
            "response": ResponseGenerator()
        }

        # Metric functions
        metrics = {
            "conflict": conflict_metric,
            "intent": intent_metric,
            "quality": quality_metric,
            "goals": goals_metric,
            "response": response_metric
        }

        # Optimize each module using teacher LLM
        optimized_modules = {}
        results = {}

        teacher_model = settings.gepa_teacher_model
        with dspy_configurator.use_teacher_lm(teacher_model):
            for module_name, baseline_module in baseline_modules.items():
                logger.info(f"🔧 Optimizing {module_name} module...")

                trainset = datasets[module_name]
                metric = metrics[module_name]

                if len(trainset) < 10:
                    logger.warning(f"⏭️  Skipping {module_name}: only {len(trainset)} examples")
                    results[module_name] = {"status": "skipped", "reason": "insufficient_data"}
                    continue

                try:
                    # Split train/val
                    split_idx = int(len(trainset) * 0.7)
                    train = trainset[:split_idx]
                    val = trainset[split_idx:]

                    # Create GEPA optimizer with teacher LLM
                    optimizer = dspy.GEPA(
                        metric=metric,
                        breadth=settings.gepa_breadth,
                        depth=settings.gepa_depth,
                        init_temperature=1.0
                    )

                    # Compile module (GEPA optimizes prompts)
                    optimized = optimizer.compile(
                        baseline_module,
                        trainset=train,
                        valset=val,
                        num_threads=4
                    )

                    optimized_modules[module_name] = optimized

                    # Evaluate on validation set
                    val_scores = []
                    for example in val[:10]:  # Sample 10
                        pred = optimized(**example.inputs().toDict())
                        score = metric(example, pred)
                        val_scores.append(score)

                    avg_score = sum(val_scores) / len(val_scores) if val_scores else 0.0
                    results[module_name] = {
                        "status": "success",
                        "avg_score": avg_score,
                        "num_examples": len(trainset),
                        "train_size": len(train),
                        "val_size": len(val)
                    }

                    logger.info(f"✅ {module_name}: score={avg_score:.3f}")

                except Exception as e:
                    logger.error(f"❌ {module_name} optimization failed: {e}")
                    results[module_name] = {"status": "error", "error": str(e)}

        # Save optimized modules with versioning
        if optimized_modules:
            version = "v1.0"  # TODO: Auto-increment version
            metadata = {
                "gepa_config": {
                    "breadth": settings.gepa_breadth,
                    "depth": settings.gepa_depth
                },
                "metrics": {
                    name: res.get("avg_score", 0.0)
                    for name, res in results.items()
                    if res.get("status") == "success"
                },
                "teacher_lm": "qwen3:8b",
                "student_lm": "gemma3:4b"
            }

            save_optimized_modules(optimized_modules, version, metadata)
            logger.info(f"💾 Saved {len(optimized_modules)} optimized modules as {version}")

        return {
            "status": "success",
            "decisions_processed": len(decisions),
            "iterations": num_iterations,
            "module_results": results,
            "optimized_count": len(optimized_modules)
        }

    except Exception as e:
        logger.error(f"❌ GEPA optimization failed: {e}")
        return {"status": "error", "error": str(e)}
