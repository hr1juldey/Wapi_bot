"""Brain database table definitions for SQLite."""

BRAIN_DECISIONS_TABLE = """
CREATE TABLE IF NOT EXISTS brain_decisions (
    decision_id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL,
    timestamp DATETIME NOT NULL,
    user_message TEXT NOT NULL,
    conversation_history TEXT,
    state_snapshot TEXT,
    conflict_detected TEXT,
    predicted_intent TEXT,
    proposed_response TEXT,
    confidence REAL,
    brain_mode TEXT NOT NULL,
    action_taken TEXT,
    response_sent TEXT,
    user_response TEXT,
    workflow_outcome TEXT,
    user_satisfaction REAL
);
"""

BRAIN_MEMORIES_TABLE = """
CREATE TABLE IF NOT EXISTS brain_memories (
    memory_id TEXT PRIMARY KEY,
    timestamp DATETIME NOT NULL,
    memory_type TEXT NOT NULL,
    context TEXT NOT NULL,
    learning TEXT NOT NULL,
    confidence REAL,
    source TEXT
);
"""

BRAIN_DREAMS_TABLE = """
CREATE TABLE IF NOT EXISTS brain_dreams (
    dream_id TEXT PRIMARY KEY,
    timestamp DATETIME NOT NULL,
    model_used TEXT NOT NULL,
    conversations_processed INTEGER,
    dreams_generated INTEGER,
    patterns_learned INTEGER,
    dream_data TEXT
);
"""
