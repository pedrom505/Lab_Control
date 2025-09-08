
from flask import Flask, request, jsonify
import ctypes
import threading
import time

# Load the C library
lib = ctypes.CDLL("/app/GPIO_Controller/GPIO_Control.so")

# Define function signatures    
lib.READ_DHT22.argtypes = [ctypes.c_int]
lib.READ_DHT22.restype = None

lib.GET_TEMPERATURE.argtypes = []
lib.GET_TEMPERATURE.restype = ctypes.c_float

lib.GET_HUMIDITY.argtypes = []
lib.GET_HUMIDITY.restype = ctypes.c_float

lib.GPIO_OUT.argtypes = [ctypes.c_int, ctypes.c_int]
lib.GPIO_OUT.restype = ctypes.c_int   # Returns status code

# Hardware configuration
SENSOR_PORT = 7
STATUS_PORT = 23
HEATER_PORT = 24
COOLER_PORT = 25

# System state
target_temperature = 25.0  # Default setpoint
auto_control_enabled = True
current_temp = 0
current_humidity = 0

app = Flask(__name__)

def status(state: bool):
    lib.GPIO_OUT(STATUS_PORT, 1 if state else 0)

def cooler(state: bool):
    lib.GPIO_OUT(COOLER_PORT, 0 if state else 1)

def heater(state: bool):
    lib.GPIO_OUT(HEATER_PORT, 1 if state else 0)

# Background thread for automatic temperature control
def temperature_control_loop():
    global target_temperature, auto_control_enabled, current_temp, current_humidity
    status(True)
    cooler(True)
    print("--- TEMPERATURE LOOP RUNNING ---")
    while True:
        lib.READ_DHT22(SENSOR_PORT)
        current_temp = lib.GET_TEMPERATURE()
        current_humidity = lib.GET_HUMIDITY()
        if auto_control_enabled:
            if current_temp > target_temperature + 0.5:
                lib.GPIO_OUT(HEATER_PORT, 0)      # Turn heater OFF
            elif current_temp < target_temperature - 0.5:
                lib.GPIO_OUT(HEATER_PORT, 1)      # Turn heater ON
        time.sleep(1)


# API to set target temperature
@app.route("/setpoint", methods=["POST"])
def set_temperature():
    global target_temperature
    data = request.get_json()
    if "value" not in data:
        return jsonify({"error": "Missing 'value' field"}), 400
    target_temperature = float(data["value"])
    return jsonify({"setpoint": target_temperature})

# API to read sensor data
@app.route("/sensor", methods=["GET"])
def read_sensor():
    return jsonify({"Temperature": current_temp, "Humidity": current_humidity})

# API to control the cooler
@app.route("/cooler", methods=["POST"])
def control_cooler():
    data = request.get_json()
    state = data.get("state")
    if state not in [True, False]:
        return jsonify({"error": "'state' must be True or False"}), 400
    cooler(state)
    return jsonify({
        "cooler": "on" if state else "off",
    })

# API to control the heater
@app.route("/heater", methods=["POST"])
def control_heater():
    data = request.get_json()
    state = data.get("state")
    if state not in [True, False]:
        return jsonify({"error": "'state' must be True or False"}), 400
    heater(state)
    return jsonify({
        "heater": "on" if state else "off",
    })

if __name__ == "__main__":
    lib.init()

    # Start the control thread
    threading.Thread(target=temperature_control_loop, daemon=True).start()
    app.run(host="192.168.15.10", port=5000)
    






