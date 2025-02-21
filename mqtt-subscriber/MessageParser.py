import os
import json
import logging
from datetime import datetime
from typing import Any, Dict

from Database import Database


class MessageParser:
    log_dir = "logs"
    log_file = os.path.join(log_dir, "messages.log")

    # Ensure logs directory exists
    os.makedirs(log_dir, exist_ok=True)

    # Ensure log file exists
    if not os.path.exists(log_file):
        open(log_file, "w").close()  # Create an empty file

    # Configure logging (INFO for valid messages, ERROR for invalid ones)
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s: %(message)s",
        encoding="utf-8",
    )

    @staticmethod
    def validate_message(message: Dict[str, Any]) -> bool:
        required_keys = {"device_id", "sensor_type", "sensor_value", "timestamp"}

        if not required_keys.issubset(message.keys()):
            logging.error(
                f"Missing keys: {required_keys - message.keys()} - Message: {message}"
            )
            return False

        if not isinstance(message["device_id"], str):
            logging.error(
                f"Invalid type for 'device_id', expected str - Message: {message}"
            )
            return False

        if not isinstance(message["sensor_type"], str):
            logging.error(
                f"Invalid type for 'sensor_type', expected str - Message: {message}"
            )
            return False

        if not isinstance(message["sensor_value"], (float, int)):
            logging.error(
                f"Invalid type for 'sensor_value', expected float - Message: {message}"
            )
            return False

        try:
            datetime.fromisoformat(message["timestamp"])
        except ValueError:
            logging.error(
                f"Invalid timestamp format, expected ISO8601 - Message: {message}"
            )
            return False

        return True

    @staticmethod
    def parse_message(json_message: str) -> Dict[str, Any]:
        try:
            message = json.loads(json_message)
        except json.JSONDecodeError:
            logging.error(f"Invalid JSON format: {json_message}")
            raise ValueError("Invalid JSON format")

        if not MessageParser.validate_message(message):
            raise ValueError("Message does not follow the required format")

        # Get current timestamp for logging
        current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Log valid message as INFO
        logging.info(f"Timestamp: {current_timestamp}, Valid Message: {message}")

        # Store in database
        db = Database()
        db.update_device_last_seen(message["device_id"], message["timestamp"])
        db.insert_event(
            message["device_id"],
            message["sensor_type"],
            message["sensor_value"],
            message["timestamp"],
        )
        print("Data stored in SQLite.")

        return message


if __name__ == "__main__":
    valid_json = """{
        "device_id": "sensor_002",
        "sensor_type": "temperature",
        "sensor_value": 22.5,
        "timestamp": "2025-02-20T23:57:54"
    }"""

    invalid_json = """{
        "device_id": 123,  
        "sensor_type": "temperature",
        "sensor_value": "invalid_float",
        "timestamp": "not-a-valid-timestamp"
    }"""

    try:
        parsed_message = MessageParser.parse_message(valid_json)
    except ValueError as e:
        print("Error:", e)

    try:
        MessageParser.parse_message(invalid_json)
    except ValueError as e:
        print("Error:", e)
