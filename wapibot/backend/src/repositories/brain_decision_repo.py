"""Brain decision repository - CRUD for RL Gym decisions."""

import sqlite3
from typing import List, Optional
from models.brain_decision import BrainDecision
from core.brain_config import get_brain_settings


class BrainDecisionRepository:
    """Repository for brain decision records."""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize repository with database path."""
        if db_path is None:
            settings = get_brain_settings()
            db_path = settings.rl_gym_db_path
        self.db_path = db_path

    def save(self, decision: BrainDecision) -> None:
        """Save brain decision to database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO brain_decisions VALUES
            (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            decision.decision_id, decision.conversation_id,
            decision.timestamp.isoformat(), decision.user_message,
            decision.conversation_history, decision.state_snapshot,
            decision.conflict_detected, decision.predicted_intent,
            decision.proposed_response, decision.confidence,
            decision.brain_mode, decision.action_taken,
            decision.response_sent, decision.user_response,
            decision.workflow_outcome, decision.user_satisfaction
        ))

        conn.commit()
        conn.close()

    def get_recent(self, limit: int = 100) -> List[BrainDecision]:
        """Get recent brain decisions."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM brain_decisions
            ORDER BY timestamp DESC LIMIT ?
        """, (limit,))

        rows = cursor.fetchall()
        conn.close()

        return [BrainDecision(**dict(row)) for row in rows]
