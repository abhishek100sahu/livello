# IoT Device API

## Overview
This Flask-based API provides endpoints to retrieve registered IoT devices and their latest event data. The API is rate-limited and stores data in an SQLite database.

## Prerequisites
- Docker and Docker Compose installed
- API running inside a containerized environment

## Running the API
To start the API using Docker Compose, run:

```sh
docker-compose up -d flask-api
```

This will start the Flask API and make it accessible on `http://localhost:5000`.

---

## API Endpoints

### 1. Get List of Devices
**Endpoint:** `/api/v1/devices`

**Method:** `GET`

**Description:** Retrieves all registered devices with their last seen timestamps.

**Rate Limit:** 50 requests per minute

**Request Example:**

```sh
curl -X GET "http://localhost:5000/api/v1/devices" -H "Accept: application/json"
```

**Response Example:**

```json
{
  "devices": [
    { "device_id": "1234", "last_seen": "2024-02-19 14:30:00" },
    { "device_id": "5678", "last_seen": "2024-02-19 14:40:00" }
  ]
}
```

---

### 2. Get Latest Events for a Device
**Endpoint:** `/api/v1/events/<device_id>`

**Method:** `GET`

**Description:** Retrieves the latest events for a given device with optional pagination.

**Rate Limit:** 50 requests per minute

**Query Parameters:**
- `limit` (optional, default=10): Number of latest events to return.
- `offset` (optional, default=0): Offset for pagination.

**Request Example:**

```sh
curl -X GET "http://localhost:5000/api/v1/events/1234?limit=5&offset=0" -H "Accept: application/json"
```

**Response Example:**

```json
{
  "events": [
    {
      "event_id": "evt-1",
      "device_id": "1234",
      "sensor_type": "temperature",
      "sensor_value": "22.5",
      "timestamp": "2024-02-19 14:35:00"
    },
    {
      "event_id": "evt-2",
      "device_id": "1234",
      "sensor_type": "humidity",
      "sensor_value": "45",
      "timestamp": "2024-02-19 14:30:00"
    }
  ]
}
```

---

## MQTT Publishing (mosquitto_pub)
To publish an MQTT message to the containerized broker, use the following command:

```sh
mosquitto_pub -h localhost -t "devices/events" -m '{"device_id": "1234", "sensor_type": "temperature", "sensor_value": "22.5"}'
```

Make sure the broker is running inside the container, and your topic is correctly set up.

---

## Handling Invalid JSON Requests
If an invalid JSON payload is sent, the API will return a `400 Bad Request` error, and it will be logged.

**Example Request with Invalid JSON:**
```sh
curl -X POST "http://localhost:5000/api/v1/events" -H "Content-Type: application/json" -d '{invalid_json}'
```

**Response Example:**
```json
{
  "transaction_id": "abcd-1234",
  "error": "Invalid JSON payload"
}
```

API logs will capture the malformed request with details for debugging.

---

## API Versioning
This API follows versioning under `/api/v1/`. Future updates will increment the version (`/api/v2/`, etc.) to ensure backward compatibility.

---

## Using Postman
1. Open **Postman**.
2. Create a new request.
3. Set the request type to **GET**.
4. Enter the URL: `http://localhost:5000/api/v1/devices`.
5. Click **Send** to get the response.

For event data:
- Change the URL to `http://localhost:5000/api/v1/events/{device_id}`
- Optionally, add query parameters for `limit` and `offset`.

---

## Logging
API logs are stored in the `logs/` directory as `api_YYYY-MM-DD.log` files.

To check logs:
```sh
tail -f logs/api_$(date +%F).log
```

---

## Stopping the API
To stop the API container:
```sh
docker-compose down
```

---

## Troubleshooting
1. **Database Errors:** Ensure `sqlite_data` volume is correctly mounted and accessible.
2. **Connection Refused:** Check if the Flask API container is running using `docker ps`.
3. **Rate Limiting Issues:** If requests are blocked, wait a minute before retrying.
4. **MQTT Issues:** Ensure the MQTT broker is running and accessible within the network.

---

