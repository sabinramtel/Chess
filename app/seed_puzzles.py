import os


def seed_puzzles_if_empty():
    """
    The `puzzles` table is created empty by db.create_all() — the actual rows
    only exist in the scripts/puzzles.sql dump. If the table has no rows
    (e.g. a fresh production database), load them from that dump so the
    puzzle page has data to serve.
    """
    from app import db
    from app.models.puzzle_model import Puzzle

    if Puzzle.query.count() > 0:
        return

    sql_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'scripts', 'puzzles.sql')
    if not os.path.isfile(sql_path):
        print(f"Puzzle seed file not found at {sql_path}, skipping seeding.")
        return

    print("Puzzles table is empty — seeding from scripts/puzzles.sql ...")
    connection = db.engine.raw_connection()
    try:
        cursor = connection.cursor()
        inserted = 0
        with open(sql_path, encoding='utf-8') as f:
            for line in f:
                if line.startswith('INSERT INTO'):
                    cursor.execute(line)
                    inserted += cursor.rowcount
        connection.commit()
        cursor.close()
        print(f"Puzzle seeding complete — {inserted:,} rows inserted.")
    except Exception as e:
        connection.rollback()
        print(f"ERROR: Puzzle seeding failed: {e}")
    finally:
        connection.close()
