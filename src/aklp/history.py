"""Session history management for REPL mode."""

import json
import uuid
from datetime import datetime
from pathlib import Path

from aklp.models import ConversationTurn, SessionHistory


class HistoryManager:
    """Manage conversation history for REPL sessions."""

    def __init__(self, history_file: Path | None = None):
        """Initialize history manager.

        Args:
            history_file: Path to history file. Defaults to ~/.aklp_history.json
        """
        if history_file is None:
            history_file = Path.home() / ".aklp_history.json"
        self.history_file = history_file
        self.current_session = SessionHistory(
            session_id=str(uuid.uuid4()),
            started_at=datetime.now(),
        )

    def add_turn(self, turn: ConversationTurn) -> None:
        """Add a conversation turn to current session.

        Args:
            turn: Conversation turn to add
        """
        self.current_session.turns.append(turn)

    def get_turns(self) -> list[ConversationTurn]:
        """Get all turns in current session.

        Returns:
            List of conversation turns
        """
        return self.current_session.turns

    def clear_history(self) -> None:
        """Clear current session history."""
        self.current_session.turns = []

    def save_session(self) -> None:
        """Save current session to history file."""
        try:
            all_sessions = []
            if self.history_file.exists():
                with open(self.history_file) as f:
                    data = json.load(f)
                    all_sessions = data.get("sessions", [])

            session_dict = self.current_session.model_dump(mode="json")
            all_sessions.append(session_dict)

            max_sessions = 100
            if len(all_sessions) > max_sessions:
                all_sessions = all_sessions[-max_sessions:]

            with open(self.history_file, "w") as f:
                json.dump({"sessions": all_sessions}, f, indent=2, default=str)

        except Exception:
            pass

    def load_last_session(self) -> SessionHistory | None:
        """Load the most recent session from history file.

        Returns:
            Last session if available, None otherwise
        """
        try:
            if not self.history_file.exists():
                return None

            with open(self.history_file) as f:
                data = json.load(f)
                sessions = data.get("sessions", [])
                if not sessions:
                    return None

                return SessionHistory.model_validate(sessions[-1])

        except Exception:
            return None

    def get_session_count(self) -> int:
        """Get total number of turns in current session.

        Returns:
            Number of conversation turns
        """
        return len(self.current_session.turns)
