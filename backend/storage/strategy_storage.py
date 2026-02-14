"""
Strategy Storage using SQLite
Stores user strategies with parameters and results
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path
import uuid


class StrategyStorage:
    """Manage strategy storage in SQLite database"""

    def __init__(self, db_path: str = "backend/storage/strategies.db"):
        """Initialize strategy storage"""
        self.db_path = db_path

        # Create directory if not exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        # Initialize database
        self._init_db()

    def _init_db(self):
        """Create database tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS strategies (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                user_id TEXT NOT NULL,
                shared INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                parameters TEXT NOT NULL,
                backtest_results TEXT,
                universe TEXT
            )
        """)

        conn.commit()
        conn.close()

    def save_strategy(
        self,
        name: str,
        parameters: Dict,
        user_id: str = "default_user",
        description: str = "",
        shared: bool = False,
        backtest_results: Dict = None,
        universe: str = "S&P 500",
    ) -> str:
        """
        Save a strategy

        Args:
            name: Strategy name
            parameters: Strategy parameters dict
            user_id: User identifier
            description: Strategy description
            shared: Whether to share with community
            backtest_results: Optional backtest results
            universe: Stock universe used

        Returns:
            Strategy ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        strategy_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()

        cursor.execute(
            """
            INSERT INTO strategies 
            (id, name, description, user_id, shared, created_at, updated_at, 
             parameters, backtest_results, universe)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                strategy_id,
                name,
                description,
                user_id,
                1 if shared else 0,
                timestamp,
                timestamp,
                json.dumps(parameters),
                json.dumps(backtest_results) if backtest_results else None,
                universe,
            ),
        )

        conn.commit()
        conn.close()

        return strategy_id

    def get_strategies(
        self, user_id: str = "default_user", include_shared: bool = True
    ) -> List[Dict]:
        """
        Get all strategies for a user

        Args:
            user_id: User identifier
            include_shared: Include shared strategies from other users

        Returns:
            List of strategy dicts
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if include_shared:
            cursor.execute(
                """
                SELECT * FROM strategies 
                WHERE user_id = ? OR shared = 1
                ORDER BY created_at DESC
                """,
                (user_id,),
            )
        else:
            cursor.execute(
                """
                SELECT * FROM strategies 
                WHERE user_id = ?
                ORDER BY created_at DESC
                """,
                (user_id,),
            )

        columns = [description[0] for description in cursor.description]
        strategies = []

        for row in cursor.fetchall():
            strategy = dict(zip(columns, row))
            strategy["parameters"] = json.loads(strategy["parameters"])
            if strategy["backtest_results"]:
                strategy["backtest_results"] = json.loads(strategy["backtest_results"])
            strategy["shared"] = bool(strategy["shared"])
            strategies.append(strategy)

        conn.close()
        return strategies

    def get_strategy(self, strategy_id: str) -> Optional[Dict]:
        """Get a single strategy by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM strategies WHERE id = ?", (strategy_id,))
        columns = [description[0] for description in cursor.description]
        row = cursor.fetchone()

        if row:
            strategy = dict(zip(columns, row))
            strategy["parameters"] = json.loads(strategy["parameters"])
            if strategy["backtest_results"]:
                strategy["backtest_results"] = json.loads(strategy["backtest_results"])
            strategy["shared"] = bool(strategy["shared"])
            conn.close()
            return strategy

        conn.close()
        return None

    def delete_strategy(self, strategy_id: str, user_id: str) -> bool:
        """Delete a strategy (only if owned by user)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "DELETE FROM strategies WHERE id = ? AND user_id = ?",
            (strategy_id, user_id),
        )

        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()

        return deleted

    def update_strategy(
        self,
        strategy_id: str,
        user_id: str,
        name: str = None,
        description: str = None,
        shared: bool = None,
    ) -> bool:
        """Update strategy metadata (only if owned by user)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        updates = []
        values = []

        if name is not None:
            updates.append("name = ?")
            values.append(name)
        if description is not None:
            updates.append("description = ?")
            values.append(description)
        if shared is not None:
            updates.append("shared = ?")
            values.append(1 if shared else 0)

        if not updates:
            return False

        updates.append("updated_at = ?")
        values.append(datetime.now().isoformat())

        values.extend([strategy_id, user_id])

        cursor.execute(
            f"""
            UPDATE strategies 
            SET {", ".join(updates)}
            WHERE id = ? AND user_id = ?
            """,
            values,
        )

        updated = cursor.rowcount > 0
        conn.commit()
        conn.close()

        return updated
