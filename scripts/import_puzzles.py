"""
Import the Lichess puzzle CSV into the puzzles table.

Usage
-----
    python scripts/import_puzzles.py <path_to_lichess_db_puzzle.csv>

Download the CSV from:  https://database.lichess.org/#puzzles
Expected columns: PuzzleId, FEN, Moves, Rating, RatingDeviation,
                  Popularity, NbPlays, Themes, GameUrl, OpeningTags

The script is idempotent — duplicate PuzzleIds are silently skipped
(INSERT IGNORE), so you can re-run it safely.
"""

import csv
import os
import sys

import pymysql
from dotenv import load_dotenv

load_dotenv()

# ── Schema ────────────────────────────────────────────────────────────────────

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS puzzles (
    id        INT          AUTO_INCREMENT PRIMARY KEY,
    puzzle_id VARCHAR(20)  NOT NULL,
    fen       TEXT         NOT NULL,
    moves     TEXT         NOT NULL,
    rating    INT          NOT NULL,
    themes    VARCHAR(500),
    UNIQUE KEY uq_puzzle_id (puzzle_id),
    INDEX      idx_rating  (rating)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""

INSERT_SQL = """
INSERT IGNORE INTO puzzles (puzzle_id, fen, moves, rating, themes)
VALUES (%s, %s, %s, %s, %s)
"""

# ── Helpers ───────────────────────────────────────────────────────────────────

def _connect() -> pymysql.Connection:
    return pymysql.connect(
        host     = os.getenv('MYSQL_HOST',     'localhost'),
        user     = os.getenv('MYSQL_USER',     'root'),
        password = os.getenv('MYSQL_PASSWORD', ''),
        database = os.getenv('MYSQL_DB',       'chess_db'),
        charset  = 'utf8mb4',
        autocommit=False,
    )


def import_csv(csv_path: str, batch_size: int = 1000) -> None:
    if not os.path.isfile(csv_path):
        print(f'File not found: {csv_path}')
        sys.exit(1)

    conn   = _connect()
    cursor = conn.cursor()

    print('Creating table if not exists...')
    cursor.execute(CREATE_TABLE_SQL)
    conn.commit()

    total = 0
    batch: list[tuple] = []

    print(f'Importing from {csv_path} ...')

    with open(csv_path, encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                rating = int(row['Rating'])
            except (ValueError, KeyError):
                continue  # skip malformed rows

            batch.append((
                row['PuzzleId'],
                row['FEN'],
                row['Moves'],
                rating,
                row.get('Themes', ''),
            ))

            if len(batch) >= batch_size:
                cursor.executemany(INSERT_SQL, batch)
                conn.commit()
                total += len(batch)
                batch  = []
                print(f'\r  {total:,} rows inserted...', end='', flush=True)

    if batch:
        cursor.executemany(INSERT_SQL, batch)
        conn.commit()
        total += len(batch)

    cursor.close()
    conn.close()
    print(f'\nDone — {total:,} puzzles imported (duplicates skipped).')


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(f'Usage: python {sys.argv[0]} <path_to_csv>')
        sys.exit(1)

    import_csv(sys.argv[1])
