"""A/B testing service for brain modules (shadow mode only).

CRITICAL: All testing happens in shadow observation. No customer impact.
"""

import random
import logging
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
from models.ab_test_result import ABTestResult

logger = logging.getLogger(__name__)


class ShadowABTester:
    """Run A/B tests on brain modules without affecting customers.

    Both variants run in shadow mode:
    - Customer sees neither variant
    - Both outputs are logged for comparison
    - Statistical analysis determines winner
    """

    def __init__(
        self,
        test_name: str,
        variant_a: str = "v0.0",
        variant_b: str = "v1.0"
    ):
        """Initialize A/B test.

        Args:
            test_name: Test identifier (e.g., "conflict_detector_v1")
            variant_a: Baseline version
            variant_b: Test version
        """
        self.test_name = test_name
        self.variant_a = variant_a
        self.variant_b = variant_b
        self.assignments: Dict[str, str] = {}  # conversation_id → variant
        self.results: List[ABTestResult] = []

    def assign_variant(self, conversation_id: str) -> str:
        """Assign conversation to variant (50/50 split).

        Args:
            conversation_id: Conversation identifier

        Returns:
            "A" or "B"
        """
        if conversation_id not in self.assignments:
            self.assignments[conversation_id] = random.choice(["A", "B"])

        return self.assignments[conversation_id]

    def run_both_variants(
        self,
        conversation_id: str,
        module_a: Any,
        module_b: Any,
        inputs: Dict[str, Any],
        metric_fn: Optional[callable] = None
    ) -> ABTestResult:
        """Run BOTH variants and compare results.

        CRITICAL: Both run in shadow mode. Customer sees neither.

        Args:
            conversation_id: Conversation identifier
            module_a: Baseline module instance
            module_b: Optimized module instance
            inputs: Module inputs
            metric_fn: Optional metric function for scoring

        Returns:
            ABTestResult with comparison
        """
        assigned_variant = self.assign_variant(conversation_id)

        try:
            # Run both variants (shadow mode)
            output_a = module_a(**inputs)
            output_b = module_b(**inputs)

            # Calculate metrics if function provided
            score_a = None
            score_b = None

            if metric_fn:
                try:
                    import dspy
                    # Create example from inputs for metric
                    example = dspy.Example(**inputs)
                    pred_a = dspy.Prediction(**output_a)
                    pred_b = dspy.Prediction(**output_b)

                    score_a = metric_fn(example, pred_a)
                    score_b = metric_fn(example, pred_b)
                except Exception as e:
                    logger.warning(f"Metric calculation failed: {e}")

            # Compare outputs
            difference = self._calculate_difference(output_a, output_b)

            # Determine winner
            winner = None
            if score_a is not None and score_b is not None:
                if score_b > score_a:
                    winner = "B"
                elif score_a > score_b:
                    winner = "A"
                else:
                    winner = "tie"

            # Create result
            result = ABTestResult(
                test_id=str(uuid.uuid4()),
                test_name=self.test_name,
                conversation_id=conversation_id,
                timestamp=datetime.utcnow(),
                assigned_variant=assigned_variant,
                variant_a=self.variant_a,
                variant_b=self.variant_b,
                variant_a_output=output_a,
                variant_b_output=output_b,
                difference=difference,
                metric_score_a=score_a,
                metric_score_b=score_b,
                winner=winner
            )

            self.results.append(result)

            logger.info(
                f"📊 A/B Test '{self.test_name}': "
                f"Variant {assigned_variant} assigned, "
                f"Scores: A={score_a:.3f if score_a else 'N/A'}, "
                f"B={score_b:.3f if score_b else 'N/A'}, "
                f"Winner={winner or 'N/A'}"
            )

            return result

        except Exception as e:
            logger.error(f"A/B test failed: {e}")
            raise

    def _calculate_difference(
        self,
        output_a: Dict[str, Any],
        output_b: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate differences between variant outputs.

        Args:
            output_a: Baseline output
            output_b: Test output

        Returns:
            Dict of differences
        """
        differences = {}

        # Compare common keys
        common_keys = set(output_a.keys()) & set(output_b.keys())

        for key in common_keys:
            val_a = output_a[key]
            val_b = output_b[key]

            if val_a != val_b:
                differences[key] = {
                    "variant_a": val_a,
                    "variant_b": val_b,
                    "changed": True
                }

        # Keys only in one variant
        only_a = set(output_a.keys()) - set(output_b.keys())
        only_b = set(output_b.keys()) - set(output_a.keys())

        if only_a:
            differences["only_in_a"] = list(only_a)
        if only_b:
            differences["only_in_b"] = list(only_b)

        return differences

    def get_statistics(self) -> Dict[str, Any]:
        """Calculate statistical summary of A/B test.

        Returns:
            Dict with statistics (mean scores, win rates, significance)
        """
        if not self.results:
            return {"error": "No results yet"}

        # Filter results with scores
        scored_results = [
            r for r in self.results
            if r.metric_score_a is not None and r.metric_score_b is not None
        ]

        if not scored_results:
            return {"error": "No scored results"}

        # Calculate means
        mean_a = sum(r.metric_score_a for r in scored_results) / len(scored_results)
        mean_b = sum(r.metric_score_b for r in scored_results) / len(scored_results)

        # Win counts
        wins_a = sum(1 for r in scored_results if r.winner == "A")
        wins_b = sum(1 for r in scored_results if r.winner == "B")
        ties = sum(1 for r in scored_results if r.winner == "tie")

        # Improvement
        improvement_pct = ((mean_b - mean_a) / mean_a * 100) if mean_a > 0 else 0.0

        # Simple significance check (t-test would be better)
        is_significant = abs(improvement_pct) > 5.0 and len(scored_results) >= 30

        return {
            "test_name": self.test_name,
            "variant_a": self.variant_a,
            "variant_b": self.variant_b,
            "sample_size": len(scored_results),
            "mean_score_a": mean_a,
            "mean_score_b": mean_b,
            "improvement_pct": improvement_pct,
            "wins_a": wins_a,
            "wins_b": wins_b,
            "ties": ties,
            "is_significant": is_significant,
            "recommended_winner": "B" if improvement_pct > 5 else "A" if improvement_pct < -5 else "tie"
        }

    def declare_winner(self, min_sample_size: int = 30) -> Optional[str]:
        """Declare winner based on statistical analysis.

        Args:
            min_sample_size: Minimum results needed for declaration

        Returns:
            "A", "B", or None if inconclusive
        """
        stats = self.get_statistics()

        if "error" in stats:
            logger.info(f"Cannot declare winner: {stats['error']}")
            return None

        if stats["sample_size"] < min_sample_size:
            logger.info(
                f"Insufficient sample size: {stats['sample_size']}/{min_sample_size}"
            )
            return None

        if not stats["is_significant"]:
            logger.info("Difference not statistically significant")
            return None

        winner = stats["recommended_winner"]

        if winner == "tie":
            logger.info("Results are too close to call a winner")
            return None

        logger.info(
            f"🏆 Winner: Variant {winner} "
            f"({stats['improvement_pct']:.1f}% improvement, "
            f"n={stats['sample_size']})"
        )

        return winner
