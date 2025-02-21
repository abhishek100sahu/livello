import os
import sqlite3


class Database:
    def __init__(self):
        # Define database location from environment variable or default to local
        self.db_path = os.getenv("DB_PATH", "/data/iot_data.db")

        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        """Creates the Devices and Events tables if they don't exist."""
        with self.conn:
            self.cursor.executescript(
                """
                CREATE TABLE IF NOT EXISTS Devices (
                    device_id TEXT PRIMARY KEY,
                    last_seen TEXT
                );

                CREATE TABLE IF NOT EXISTS Events (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT,
                    sensor_type TEXT,
                    sensor_value REAL,
                    timestamp TEXT,
                    FOREIGN KEY (device_id) REFERENCES Devices(device_id)
                );

                CREATE INDEX IF NOT EXISTS idx_timestamp ON Events (timestamp);
                CREATE INDEX IF NOT EXISTS idx_device ON Events (device_id);
                """
            )

    def update_device_last_seen(self, device_id: str, timestamp: str):
        """Updates the last seen timestamp of a device."""
        with self.conn:
            self.cursor.execute(
                """
                INSERT INTO Devices (device_id, last_seen) 
                VALUES (?, ?)
                ON CONFLICT(device_id) 
                DO UPDATE SET last_seen=excluded.last_seen;
                """,
                (device_id, timestamp),
            )

    def insert_event(
        self, device_id: str, sensor_type: str, sensor_value: float, timestamp: str
    ):
        """Inserts a new event record."""
        with self.conn:
            self.cursor.execute(
                """
                INSERT INTO Events (device_id, sensor_type, sensor_value, timestamp) 
                VALUES (?, ?, ?, ?);
                """,
                (device_id, sensor_type, sensor_value, timestamp),
            )

    def close(self):
        """Closes the database connection."""
        if self.conn:
            self.conn.close()
