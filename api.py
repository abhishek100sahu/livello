from flask import Flask, jsonify, request, g
import sqlite3
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)

# Configure Rate Limiting
limiter = Limiter(get_remote_address, app=app, default_limits=["100 per minute"])  # 100 requests/min per IP

DB_PATH = "iot_data.db"

# API Versioning
API_PREFIX = "/api/v1"


def get_db_connection():
    """Creates a connection to the SQLite database and caches it in Flask's `g` object."""
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row  # Enables dict-like row access
    return g.db


@app.teardown_appcontext
def close_db_connection(exception):
    """Closes the database connection at the end of the request."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


@app.route(f"{API_PREFIX}/devices", methods=["GET"])
@limiter.limit("50 per minute")  # Limit to 50 requests per minute
def list_devices():
    """
    Retrieves all registered devices with their last seen timestamps.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT device_id, last_seen FROM Devices ORDER BY last_seen DESC;")
    devices = cursor.fetchall()

    return jsonify([dict(device) for device in devices]), 200


@app.route(f"{API_PREFIX}/events/<device_id>", methods=["GET"])
@limiter.limit("50 per minute")  # Limit API usage
def get_latest_events(device_id):
    """
    Retrieves the latest events for a given device with pagination support.
    Query parameters:
        - `limit` (optional, default=10): Number of latest events to return.
        - `offset` (optional, default=0): Offset for pagination.
    """
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
        return jsonify({"message": "No events found for this device."}), 404

    return jsonify([dict(event) for event in events]), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
