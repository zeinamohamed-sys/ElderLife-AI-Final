"""Apply database/migrations/*.sql in order (0001 and later that are not marked PLANNED). Usage: python database/init_db.py [sqlite_path]
For PostgreSQL run the same files with psql -f. Tracks applied files in schema_migrations."""
import sqlite3, sys, pathlib
mig = pathlib.Path(__file__).parent / "migrations"
db = sqlite3.connect(sys.argv[1] if len(sys.argv) > 1 else "elderlife.db")
db.execute("PRAGMA foreign_keys=ON"); db.execute("CREATE TABLE IF NOT EXISTS schema_migrations(name TEXT PRIMARY KEY)")
done = {r[0] for r in db.execute("SELECT name FROM schema_migrations")}
for f in sorted(mig.glob("*.sql")):
    sql = f.read_text(encoding="utf-8")
    if f.name in done or "PLANNED, NOT USED" in sql: continue
    db.executescript(sql); db.execute("INSERT INTO schema_migrations VALUES (?)", (f.name,)); print("applied", f.name)
db.commit()
