import os
import json
import logging
import sqlite3
import uuid
from datetime import datetime
from logging.handlers import RotatingFileHandler
from flask import Flask, jsonify, request, g
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)

# Configure Rate Limiting
limiter = Limiter(get_remote_address, app=app, default_limits=["100 per minute"])

# Get Database Path from Environment Variables
DB_PATH = os.getenv("DB_PATH", "/data/iot_data.db")

# API Versioning
API_PREFIX = "/api/v1"

# Ensure logs directory exists
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# Configure Logging
log_file = os.path.join(LOG_DIR, f"api_{datetime.now().strftime('%Y-%m-%d')}.log")
handler = RotatingFileHandler(log_file, maxBytes=5 * 1024 * 1024, backupCount=3)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(handler)

logger.info("Flask API Started")


def log_request_response(
    transaction_id: str, endpoint: str, status_code: int, response_data: dict
) -> None:
    """
    Logs API request and response details with a unique transaction ID.
    """
    log_entry = {
        "transaction_id": transaction_id,
        "endpoint": endpoint,
        "method": request.method,
        "ip": request.remote_addr,
        "status_code": status_code,
        "request_params": request.args.to_dict(),
        "request_body": request.json if request.is_json else None,
        "response_data": response_data,
    }
    logger.info(json.dumps(log_entry, indent=2))


def get_db_connection() -> sqlite3.Connection:
    """
    Creates a connection to the SQLite database and caches it in Flask's `g` object.
    """
    if "db" not in g:
        try:
            g.db = sqlite3.connect(DB_PATH)
            g.db.row_factory = sqlite3.Row  # Enables dict-like row access
        except sqlite3.DatabaseError as db_error:
            logger.error(f"Database Error: {str(db_error)}", exc_info=True)
            raise
    return g.db


@app.teardown_appcontext
def close_db_connection(exception) -> None:
    """
    Closes the database connection at the end of the request.
    """
    db = g.pop("db", None)
    if db is not None:
        db.close()


@app.route(f"{API_PREFIX}/devices", methods=["GET"])
@limiter.limit("50 per minute")
def list_devices() -> tuple:
    """
    Retrieves all registered devices with their last seen timestamps.

    :return: JSON response containing the list of devices or an error message.
    """
    transaction_id = str(uuid.uuid4())  # Generate transaction ID

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT device_id, last_seen FROM Devices ORDER BY last_seen DESC;"
        )
        devices = cursor.fetchall()

        response_data = {
            "devices": [dict(device) for device in devices],
        }
        log_request_response(transaction_id, "/devices", 200, response_data)
        return jsonify(response_data), 200

    except sqlite3.DatabaseError as db_err:
        logger.error(
            f"Transaction ID: {transaction_id} - Database Error: {str(db_err)}",
            exc_info=True,
        )
        return (
            jsonify({"transaction_id": transaction_id, "error": "Database error"}),
            500,
        )

    except Exception as e:
        logger.error(
            f"Transaction ID: {transaction_id} - Error: {str(e)}", exc_info=True
        )
        return (
            jsonify(
                {"transaction_id": transaction_id, "error": "Internal server error"}
            ),
            500,
        )


@app.route(f"{API_PREFIX}/events/<device_id>", methods=["GET"])
@limiter.limit("50 per minute")
def get_latest_events(device_id: str) -> tuple:
    """
    Retrieves the latest events for a given device with pagination support.

    Query parameters:
        - `limit` (optional, default=10): Number of latest events to return.
        - `offset` (optional, default=0): Offset for pagination.

    :param device_id: The ID of the device for which events are requested.
    :return: JSON response containing the list of events or an error message.
    """
    transaction_id = str(uuid.uuid4())  # Generate transaction ID

    try:
        limit = request.args.get("limit", 10, type=int)
        offset = request.args.get("offset", 0, type=int)

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT event_id, device_id, sensor_type, sensor_value, timestamp 
            FROM Events WHERE device_id = ? 
            ORDER BY timestamp DESC 
            LIMIT ? OFFSET ?;
            """,
            (device_id, limit, offset),
        )
        events = cursor.fetchall()

        if not events:
            response = {
                "transaction_id": transaction_id,
                "message": "No events found for this device.",
            }
            log_request_response(transaction_id, f"/events/{device_id}", 404, response)
            return jsonify(response), 404

        response_data = {
            "transaction_id": transaction_id,
            "events": [dict(event) for event in events],
        }
        log_request_response(transaction_id, f"/events/{device_id}", 200, response_data)
        return jsonify(response_data), 200

    except sqlite3.DatabaseError as db_err:
        logger.error(
            f"Transaction ID: {transaction_id} - Database Error: {str(db_err)}",
            exc_info=True,
        )
        return (
            jsonify({"transaction_id": transaction_id, "error": "Database error"}),
            500,
        )

    except Exception as e:
        logger.error(
            f"Transaction ID: {transaction_id} - Error: {str(e)}", exc_info=True
        )
        return (
            jsonify(
                {"transaction_id": transaction_id, "error": "Internal server error"}
            ),
            500,
        )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
