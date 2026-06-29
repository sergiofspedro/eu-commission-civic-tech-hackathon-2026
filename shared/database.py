"""SQLite vote and opinion storage. DB file lives at /data/civicconnect.db in container."""
import hashlib, os, sqlite3
from datetime import datetime

DB_PATH = os.environ.get("DB_PATH", "/data/civicconnect.db")


def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS votes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_hash TEXT NOT NULL,
                consultation_id TEXT NOT NULL,
                vote TEXT NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE(user_hash, consultation_id)
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS opinions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_hash TEXT NOT NULL,
                consultation_id TEXT NOT NULL,
                text TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)


def _hash(user_id: str) -> str:
    return hashlib.sha256(f"civicconnect:{user_id}".encode()).hexdigest()[:16]


def record_vote(user_id: str, consultation_id: str, vote: str) -> bool:
    """Returns True if vote was recorded, False if user already voted."""
    h = _hash(str(user_id))
    try:
        with _conn() as c:
            c.execute(
                "INSERT INTO votes (user_hash, consultation_id, vote, created_at) VALUES (?,?,?,?)",
                (h, consultation_id, vote, datetime.utcnow().isoformat()),
            )
        return True
    except sqlite3.IntegrityError:
        return False


def record_opinion(user_id: str, consultation_id: str, text: str):
    h = _hash(str(user_id))
    with _conn() as c:
        c.execute(
            "INSERT INTO opinions (user_hash, consultation_id, text, created_at) VALUES (?,?,?,?)",
            (h, consultation_id, text, datetime.utcnow().isoformat()),
        )


def has_voted(user_id: str, consultation_id: str) -> bool:
    h = _hash(str(user_id))
    with _conn() as c:
        row = c.execute(
            "SELECT 1 FROM votes WHERE user_hash=? AND consultation_id=?", (h, consultation_id)
        ).fetchone()
    return row is not None


def has_voted_all(user_id: str, consultation_ids: list) -> bool:
    return all(has_voted(user_id, cid) for cid in consultation_ids)


def get_vote_counts(consultation_id: str) -> dict:
    with _conn() as c:
        rows = c.execute(
            "SELECT vote, COUNT(*) as n FROM votes WHERE consultation_id=? GROUP BY vote",
            (consultation_id,),
        ).fetchall()
    return {row["vote"]: row["n"] for row in rows}


def get_total_participants() -> int:
    with _conn() as c:
        row = c.execute("SELECT COUNT(DISTINCT user_hash) as n FROM votes").fetchone()
    return row["n"] if row else 0
