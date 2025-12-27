"""Response generator module - dlPFC-like function (dorsolateral Prefrontal Cortex)."""

import logging
from typing import List, Dict, Any
import dspy
from dspy_signatures.brain.response_proposal_signature import ResponseProposalSignature

logger = logging.getLogger(__name__)


class ResponseRefineSignature(dspy.Signature):
    """Signature for refining a proposed response."""

    proposed_response: str = dspy.InputField(desc="Initial response to refine")
    conversation_history: str = dspy.InputField(desc="Conversation context")
    user_message: str = dspy.InputField(desc="User's message")
    sub_goals: str = dspy.InputField(desc="Sub-goals to achieve")
    feedback: str = dspy.InputField(desc="What to improve")

    refined_response: str = dspy.OutputField(desc="Improved response")
    improvements_made: str = dspy.OutputField(desc="What was improved")


class ResponseGenerator(dspy.Module):
    """Generates optimal responses using BestOfN + Refine pattern.

    Process:
    1. Generate N candidate responses
    2. Evaluate each candidate
    3. Select best candidate
    4. Refine the best response
    """

    def __init__(self, num_candidates: int = 3):
        """Initialize response generator.

        Args:
            num_candidates: Number of candidates to generate
        """
        super().__init__()
        self.num_candidates = num_candidates
        self.proposer = dspy.ChainOfThought(ResponseProposalSignature)
        self.refiner = dspy.ChainOfThought(ResponseRefineSignature)

    def _evaluate_response(self, response: str, sub_goals: List[str]) -> float:
        """Evaluate response quality (0.0-1.0).

        Heuristic scoring:
        - Addresses sub-goals: +0.3 per goal (max 0.6)
        - Length appropriate (50-200 chars): +0.2
        - Polite tone (has greeting/emoji): +0.1
        - Clear call-to-action: +0.1
        """
        score = 0.0

        # Check sub-goal coverage (max 0.6)
        goals_addressed = sum(
            1 for goal in sub_goals[:2]  # Check first 2 goals
            if any(keyword in response.lower() for keyword in goal.lower().split())
        )
        score += min(0.6, goals_addressed * 0.3)

        # Length check (0.2)
        if 50 <= len(response) <= 200:
            score += 0.2

        # Polite tone (0.1)
        if any(char in response for char in ["👋", "😊", "✅", "🎉"]):
            score += 0.1

        # Call-to-action (0.1)
        if any(word in response.lower() for word in ["?", "please", "can you", "would you"]):
            score += 0.1

        return min(1.0, score)

    def forward(
        self,
        conversation_history: List[Dict[str, str]],
        user_message: str,
        sub_goals: List[str],
        booking_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate optimal response using BestOfN + Refine.

        Args:
            conversation_history: Previous messages
            user_message: Current user message
            sub_goals: Goals to achieve in response
            booking_state: Current booking progress

        Returns:
            Dict with proposed_response, confidence, reasoning
        """
        try:
            # Format inputs
            history_str = "\n".join([
                f"{msg['role']}: {msg['content']}"
                for msg in conversation_history[-5:]
            ])

            sub_goals_str = ", ".join(sub_goals)

            state_str = f"Profile: {booking_state.get('has_profile', False)}, "
            state_str += f"Service: {booking_state.get('has_service', False)}"

            # STEP 1: Generate N candidates
            candidates = []
            for i in range(self.num_candidates):
                result = self.proposer(
                    conversation_history=history_str,
                    user_message=user_message,
                    sub_goals=sub_goals_str,
                    booking_state=state_str
                )
                candidates.append({
                    "response": result.proposed_response,
                    "reasoning": result.reasoning,
                    "score": self._evaluate_response(result.proposed_response, sub_goals)
                })

            # STEP 2: Select best candidate
            best = max(candidates, key=lambda x: x["score"])

            # STEP 3: Refine best candidate
            refined = self.refiner(
                proposed_response=best["response"],
                conversation_history=history_str,
                user_message=user_message,
                sub_goals=sub_goals_str,
                feedback="Make it more concise and friendly. Ensure clarity."
            )

            return {
                "proposed_response": refined.refined_response,
                "confidence": best["score"],
                "reasoning": f"{best['reasoning']} | Refined: {refined.improvements_made}"
            }

        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            return {
                "proposed_response": "I apologize, could you please repeat that?",
                "confidence": 0.0,
                "reasoning": f"Error: {str(e)}"
            }
