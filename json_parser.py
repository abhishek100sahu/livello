import json
import sqlite3
import logging
from datetime import datetime
from typing import Dict, Any

# Configure logging for invalid messages
logging.basicConfig(
    filename="invalid_messages.log",
    level=logging.ERROR,
    format="%(asctime)s - ERROR: %(message)s",
)


class Database:
    def __init__(self, db_name: str = "iot_data.db"):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        """Creates the Devices and Events tables if they don't exist."""
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
        self.conn.commit()

    def update_device_last_seen(self, device_id: str, timestamp: str):
        """Updates the last seen timestamp of a device."""
        self.cursor.execute(
            """
            INSERT INTO Devices (device_id, last_seen) 
            VALUES (?, ?)
            ON CONFLICT(device_id) DO UPDATE SET last_seen=excluded.last_seen;
            """,
            (device_id, timestamp),
        )
        self.conn.commit()

    def insert_event(self, device_id: str, sensor_type: str, sensor_value: float, timestamp: str):
        """Inserts a new event record."""
        self.cursor.execute(
            """
            INSERT INTO Events (device_id, sensor_type, sensor_value, timestamp) 
            VALUES (?, ?, ?, ?);
            """,
            (device_id, sensor_type, sensor_value, timestamp),
        )
        self.conn.commit()

    def close(self):
        """Closes the database connection."""
        self.conn.close()


class MessageParser:
    @staticmethod
    def validate_message(message: Dict[str, Any]) -> bool:
        """
        Validates if the given message follows the required format.

        :param message: Dictionary containing message data
        :return: True if valid, False otherwise
        """
        required_keys = {"device_id", "sensor_type", "sensor_value", "timestamp"}

        # Check for missing keys
        if not required_keys.issubset(message.keys()):
            logging.error(f"Missing keys: {required_keys - message.keys()} - Message: {message}")
            return False

        # Validate data types
        if not isinstance(message["device_id"], str):
            logging.error(f"Invalid type for 'device_id', expected str - Message: {message}")
            return False
        if not isinstance(message["sensor_type"], str):
            logging.error(f"Invalid type for 'sensor_type', expected str - Message: {message}")
            return False
        if not isinstance(message["sensor_value"], (float, int)):  # Allow int as valid float
            logging.error(f"Invalid type for 'sensor_value', expected float - Message: {message}")
            return False

        # Validate timestamp format (ISO8601)
        try:
            datetime.fromisoformat(message["timestamp"])
        except ValueError:
            logging.error(f"Invalid timestamp format, expected ISO8601 - Message: {message}")
            return False

        return True

    @staticmethod
    def parse_message(json_message: str) -> Dict[str, Any]:
        """
        Parses a JSON string message and validates its format.

        :param json_message: JSON string message
        :return: Parsed message dictionary if valid, raises ValueError otherwise
        """
        try:
            message = json.loads(json_message)
        except json.JSONDecodeError:
            logging.error(f"Invalid JSON format: {json_message}")
            raise ValueError("Invalid JSON format")

        if not MessageParser.validate_message(message):
            raise ValueError("Message does not follow the required format")

        return message


# Example Usage
if __name__ == "__main__":
    db = Database()

    valid_json = '''{
        "device_id": "sensor_001",
        "sensor_type": "temperature",
        "sensor_value": 22.5,
        "timestamp": "2024-02-19T12:34:56"
    }'''

    invalid_json = '''{
        "device_id": 123,  
        "sensor_type": "temperature",
        "sensor_value": "invalid_float",
        "timestamp": "not-a-valid-timestamp"
    }'''

    try:
        parsed_message = MessageParser.parse_message(valid_json)
        print("✅ Parsed Message:", parsed_message)

        # Store in database
        db.update_device_last_seen(parsed_message["device_id"], parsed_message["timestamp"])
        db.insert_event(
            parsed_message["device_id"],
            parsed_message["sensor_type"],
            parsed_message["sensor_value"],
            parsed_message["timestamp"],
        )
        print("✅ Data stored in SQLite.")
    except ValueError as e:
        print("❌ Error:", e)

    try:
        MessageParser.parse_message(invalid_json)
    except ValueError as e:
        print("❌ Error:", e)

    print("🚀 Check 'invalid_messages.log' for error details!")

    db.close()
