import sqlite3


def init_db(db_path: str):
    """
    Reinitializes the database with some dummy data to simulate account creation and a general workflow.
    """
    db = sqlite3.connect(db_path)

    from configs import init_db_script

    try:
        db.execute("PRAGMA foreign_keys = ON")

        db.executescript(init_db_script)
        print("Database reset successfully.")
        print("Manager account (ID 10) preserved.")

    except sqlite3.Error:
        if db.in_transaction:
            db.rollback()

        print("Database reset failed.")
        raise

    finally:
        db.close()
