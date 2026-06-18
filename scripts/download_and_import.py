"""
Download the Lichess puzzle CSV (compressed), decompress on the fly,
and import directly into the puzzles table — no temp file needed.

Usage:
    python scripts/download_and_import.py            # imports first 50,000 puzzles
    python scripts/download_and_import.py 10000      # imports first N puzzles
"""

import csv
import io
import os
import sys

import pymysql
import requests
import zstandard as zstd
from dotenv import load_dotenv

load_dotenv()

URL        = 'https://database.lichess.org/lichess_db_puzzle.csv.zst'
BATCH_SIZE = 500

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


def connect():
    return pymysql.connect(
        host      = os.getenv('MYSQL_HOST',     'localhost'),
        user      = os.getenv('MYSQL_USER',     'root'),
        password  = os.getenv('MYSQL_PASSWORD', ''),
        database  = os.getenv('MYSQL_DB',       'chess_db'),
        charset   = 'utf8mb4',
        autocommit= False,
    )


def run(limit: int = 50_000):
    conn   = connect()
    cursor = conn.cursor()
    cursor.execute(CREATE_TABLE_SQL)
    conn.commit()

    print(f'Downloading from Lichess (importing up to {limit:,} puzzles)...')
    print('This may take a minute — please wait.\n')

    response = requests.get(URL, stream=True, timeout=300)
    response.raise_for_status()

    dctx       = zstd.ZstdDecompressor()
    reader     = dctx.stream_reader(response.raw)
    text_stream = io.TextIOWrapper(reader, encoding='utf-8')
    csv_reader  = csv.DictReader(text_stream)

    total = 0
    batch = []

    for row in csv_reader:
        if total >= limit:
            break
        try:
            rating = int(row['Rating'])
        except (ValueError, KeyError):
            continue

        batch.append((
            row['PuzzleId'],
            row['FEN'],
            row['Moves'],
            rating,
            row.get('Themes', ''),
        ))

        if len(batch) >= BATCH_SIZE:
            cursor.executemany(INSERT_SQL, batch)
            conn.commit()
            total += len(batch)
            batch  = []
            print(f'\r  {total:,} puzzles imported...', end='', flush=True)

    if batch:
        cursor.executemany(INSERT_SQL, batch)
        conn.commit()
        total += len(batch)

    cursor.close()
    conn.close()
    print(f'\n\nDone! {total:,} puzzles are now in your database.')
    print('Start the server and click "START PUZZLE" on the home page.')


if __name__ == '__main__':
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 50_000
    run(limit)
