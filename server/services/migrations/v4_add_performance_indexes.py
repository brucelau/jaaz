from . import Migration
import sqlite3


class V4AddPerformanceIndexes(Migration):
    version = 4
    description = "Add performance indexes"

    def up(self, conn: sqlite3.Connection) -> None:
        conn.execute("CREATE INDEX IF NOT EXISTS idx_chat_sessions_canvas ON chat_sessions(canvas_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_chat_messages_session ON chat_messages(session_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_canvases_updated ON canvases(updated_at DESC)")

    def down(self, conn: sqlite3.Connection) -> None:
        pass
