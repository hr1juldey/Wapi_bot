"""Dataset builder for GEPA optimization.

Converts BrainDecision records to DSPy Examples for training.
"""

import json
import logging
from typing import List, Dict
import dspy
from models.brain_decision import BrainDecision
from repositories.brain_decision_repo import BrainDecisionRepository

logger = logging.getLogger(__name__)


class DatasetBuilder:
    """Convert BrainDecisions to DSPy training examples."""

    def __init__(self, repo: BrainDecisionRepository):
        """Initialize with repository.

        Args:
            repo: Repository for accessing brain decisions
        """
        self.repo = repo

    def build_conflict_dataset(self, decisions: List[BrainDecision]) -> List[dspy.Example]:
        """Build dataset for ConflictDetector module.

        Args:
            decisions: List of brain decisions

        Returns:
            List of DSPy examples with inputs and labels
        """
        examples = []

        for decision in decisions:
            try:
                history = json.loads(decision.conversation_history)

                example = dspy.Example(
                    # Inputs
                    conversation_history=history,
                    user_message=decision.user_message,
                    # Labels for metric
                    conflict_detected=decision.conflict_detected,
                    workflow_outcome=decision.workflow_outcome
                ).with_inputs("conversation_history", "user_message")

                examples.append(example)

            except json.JSONDecodeError:
                logger.warning(f"Failed to parse history for {decision.decision_id}")
                continue

        logger.info(f"Built {len(examples)} conflict examples")
        return examples

    def build_intent_dataset(self, decisions: List[BrainDecision]) -> List[dspy.Example]:
        """Build dataset for IntentPredictor module."""
        examples = []

        for decision in decisions:
            try:
                history = json.loads(decision.conversation_history)
                state = json.loads(decision.state_snapshot)

                example = dspy.Example(
                    # Inputs
                    conversation_history=history,
                    user_message=decision.user_message,
                    booking_state=state,
                    # Labels
                    predicted_intent=decision.predicted_intent,
                    action_taken=decision.action_taken,
                    workflow_outcome=decision.workflow_outcome
                ).with_inputs("conversation_history", "user_message", "booking_state")

                examples.append(example)

            except json.JSONDecodeError:
                logger.warning(f"Failed to parse data for {decision.decision_id}")
                continue

        logger.info(f"Built {len(examples)} intent examples")
        return examples

    def build_quality_dataset(self, decisions: List[BrainDecision]) -> List[dspy.Example]:
        """Build dataset for QualityEvaluator module."""
        examples = []

        for decision in decisions:
            try:
                history = json.loads(decision.conversation_history)
                state = json.loads(decision.state_snapshot)

                example = dspy.Example(
                    # Inputs
                    conversation_history=history,
                    booking_state=state,
                    # Labels
                    user_satisfaction=decision.user_satisfaction,
                    workflow_outcome=decision.workflow_outcome,
                    conflict_detected=decision.conflict_detected
                ).with_inputs("conversation_history", "booking_state")

                examples.append(example)

            except json.JSONDecodeError:
                continue

        logger.info(f"Built {len(examples)} quality examples")
        return examples

    def build_goals_dataset(self, decisions: List[BrainDecision]) -> List[dspy.Example]:
        """Build dataset for GoalDecomposer module."""
        examples = []

        for decision in decisions:
            try:
                state = json.loads(decision.state_snapshot)

                example = dspy.Example(
                    # Inputs
                    user_message=decision.user_message,
                    predicted_intent=decision.predicted_intent or "unclear",
                    booking_state=state,
                    # Labels
                    action_taken=decision.action_taken,
                    state_snapshot=decision.state_snapshot,
                    workflow_outcome=decision.workflow_outcome
                ).with_inputs("user_message", "predicted_intent", "booking_state")

                examples.append(example)

            except json.JSONDecodeError:
                continue

        logger.info(f"Built {len(examples)} goals examples")
        return examples

    def build_response_dataset(self, decisions: List[BrainDecision]) -> List[dspy.Example]:
        """Build dataset for ResponseGenerator module."""
        examples = []

        for decision in decisions:
            try:
                history = json.loads(decision.conversation_history)
                state = json.loads(decision.state_snapshot)

                # Only include if we have response
                if not decision.proposed_response:
                    continue

                example = dspy.Example(
                    # Inputs
                    conversation_history=history,
                    user_message=decision.user_message,
                    sub_goals=["continue_conversation"],  # Placeholder
                    booking_state=state,
                    # Labels
                    user_satisfaction=decision.user_satisfaction,
                    workflow_outcome=decision.workflow_outcome,
                    response_sent=decision.response_sent
                ).with_inputs("conversation_history", "user_message", "sub_goals", "booking_state")

                examples.append(example)

            except json.JSONDecodeError:
                continue

        logger.info(f"Built {len(examples)} response examples")
        return examples

    def build_all_datasets(self, num_decisions: int = 100) -> Dict[str, List[dspy.Example]]:
        """Build datasets for all 5 modules.

        Args:
            num_decisions: Number of recent decisions to use

        Returns:
            Dict mapping module name to examples list
        """
        decisions = self.repo.get_recent(num_decisions)

        logger.info(f"📊 Building datasets from {len(decisions)} decisions")

        datasets = {
            "conflict": self.build_conflict_dataset(decisions),
            "intent": self.build_intent_dataset(decisions),
            "quality": self.build_quality_dataset(decisions),
            "goals": self.build_goals_dataset(decisions),
            "response": self.build_response_dataset(decisions)
        }

        total_examples = sum(len(ds) for ds in datasets.values())
        logger.info(f"✅ Built {total_examples} total examples across 5 modules")

        return datasets
