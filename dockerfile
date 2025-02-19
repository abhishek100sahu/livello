# Use the official Eclipse Mosquitto image
FROM eclipse-mosquitto:latest

# Copy custom Mosquitto config file into the container
COPY ./mosquitto.conf /mosquitto/config/mosquitto.conf

# Expose default MQTT ports
EXPOSE 1883 9001

# Start Mosquitto
CMD ["/usr/sbin/mosquitto", "-c", "/mosquitto/config/mosquitto.conf"]
