from flask import Flask, jsonify, request
import sqlite3

app = Flask(__name__)

DB_PATH = "iot_data.db"


def get_db_connection():
    """Creates a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Enable dict-like row access
    return conn


@app.route("/devices", methods=["GET"])
def list_devices():
    """
    Retrieves all registered devices with their last seen timestamps.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT device_id, last_seen FROM Devices ORDER BY last_seen DESC;")
    devices = cursor.fetchall()

    conn.close()

    return jsonify([dict(device) for device in devices]), 200


@app.route("/events/<device_id>", methods=["GET"])
def get_latest_events(device_id):
    """
    Retrieves the latest events for a given device.
    Query parameters:
        - `limit` (optional, default=10): Number of latest events to return.
    """
    limit = request.args.get("limit", 10, type=int)

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT event_id, device_id, sensor_type, sensor_value, timestamp 
        FROM Events WHERE device_id = ? 
        ORDER BY timestamp DESC 
        LIMIT ?;
        """,
        (device_id, limit),
    )
    events = cursor.fetchall()

    conn.close()

    if not events:
        return jsonify({"message": "No events found for this device."}), 404

    return jsonify([dict(event) for event in events]), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
