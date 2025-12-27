"""Goal decomposition signature - breaks down user intent into sub-goals."""

import dspy


class GoalDecompositionSignature(dspy.Signature):
    """Decompose user intent into sub-goals (aPFC-like function).

    Breaks complex user requests into actionable steps.
    """

    user_message = dspy.InputField(
        desc="User's message or request"
    )
    current_state = dspy.InputField(
        desc="Current booking state"
    )

    main_goal = dspy.OutputField(
        desc="Primary goal identified"
    )
    sub_goals = dspy.OutputField(
        desc="List of sub-goals/steps needed (JSON array)"
    )
    required_data = dspy.OutputField(
        desc="Data needed to achieve goals (JSON array)"
    )
