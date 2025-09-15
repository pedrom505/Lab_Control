
from flask import Flask, request, jsonify
import ctypes
import threading
import time
import json
from datetime import datetime, timedelta
import atexit
import signal
import sys
import os

# Load the C library
lib = ctypes.CDLL("/app/GPIO_Controller/GPIO_Control.so")
file_path = 'sensor_data.json'

last_write_time = datetime.now()

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
STATUS_PORT = 22
COOLER_TOP_PORT = 23
COOLER_PORT = 24
HEATER_PORT = 25

# System state
target_temperature = 25.0  # Default setpoint
auto_control = False
running = True
cooler_status = False
heater_status = False
cooler_top_status = False

current_temp = 0
current_humidity = 0


thread_obj = None


app = Flask(__name__)


def write_data():
    global  current_temp, current_humidity, file_path 
    entry = {
        "TimeStamp": datetime.now().isoformat(),
        "Temperature": current_temp,
        "Humidity": current_humidity
    }

    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        data = []

    data.append(entry)

    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)


def status(state: bool):
    lib.GPIO_OUT(STATUS_PORT, 1 if state else 0)

def cooler(state: bool):
    global cooler_status
    lib.GPIO_OUT(COOLER_PORT, 1 if state else 0)
    cooler_status = state

def cooler_top(state: bool):
    global cooler_top_status
    lib.GPIO_OUT(COOLER_TOP_PORT, 1 if state else 0)
    cooler_top_status = state

def heater(state: bool):
    global heater_status
    lib.GPIO_OUT(HEATER_PORT, 1 if state else 0)
    heater_status = state

def auto_control_state(state: bool):
    global auto_control
    auto_control = state

# Background thread for automatic temperature control
def temperature_control_loop():
    global target_temperature, auto_control, current_temp, current_humidity, running, last_write_time 
    status(True)
    cooler(True)
    cooler_top(True)
    print("--- TEMPERATURE LOOP RUNNING ---")
    while running:
        lib.READ_DHT22(SENSOR_PORT)
        current_temp = lib.GET_TEMPERATURE()
        current_humidity = lib.GET_HUMIDITY()
        if auto_control:
            if current_temp > target_temperature + 0.5:
                heater(False)
            elif current_temp < target_temperature - 0.5:
                heater(True)
        
        current_time = datetime.now()
        if current_time - last_write_time >= timedelta(seconds=30):
            write_data()
            last_write_time = current_time

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
@app.route("/status", methods=["GET"])
def read_sensor():
    global cooler_status, heater_status, cooler_top_status, auto_control, target_temperature
    return jsonify(
        {
            "Temperature": current_temp, 
            "Humidity": current_humidity,
            "Cooler": "on" if cooler_status else "off",
            "Cooler_Top": "on" if cooler_top_status else "off",
            "Heater": "on" if heater_status else "off",
            "Auto_Control":  "on" if auto_control else "off",
            "Setpoint": target_temperature
         })

@app.route("/history", methods=["GET"])
def history():
    global   file_path 
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        data = []

    timestamps = [entry["TimeStamp"] for entry in data]
    temperatures = [entry["Temperature"] for entry in data]
    humidities = [entry["Humidity"] for entry in data]

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Histórico de Temperatura e Umidade</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    </head>
    <body>
        <h2>Histórico de Temperatura e Umidade</h2>
        <canvas id="chart" width="900" height="400"></canvas>
        <script>
            const ctx = document.getElementById('chart').getContext('2d');
            const chart = new Chart(ctx, {{
                type: 'line',
                data: {{
                    labels: {timestamps},
                    datasets: [
                        {{
                            label: 'Temperatura (°C)',
                            data: {temperatures},
                            borderColor: 'red',
                            backgroundColor: 'rgba(255,0,0,0.1)',
                            fill: false,
                            yAxisID: 'y',
                        }},
                        {{
                            label: 'Umidade (%)',
                            data: {humidities},
                            borderColor: 'blue',
                            backgroundColor: 'rgba(0,0,255,0.1)',
                            fill: false,
                            yAxisID: 'y1',
                        }}
                    ]
                }},
                options: {{
                    scales: {{
                        x: {{
                            title: {{
                                display: true,
                                text: 'Horário'
                            }},
                            ticks: {{
                                maxTicksLimit: 20,
                                autoSkip: true
                            }}
                        }},
                        y: {{
                            title: {{
                                display: true,
                                text: 'Temperatura (°C)'
                            }},
                            position: 'left',
                        }},
                        y1: {{
                            title: {{
                                display: true,
                                text: 'Umidade (%)'
                            }},
                            position: 'right',
                            grid: {{
                                drawOnChartArea: false
                            }}
                        }}
                    }}
                }}
            }});
        </script>
    </body>
    </html>
    """.format(
        timestamps=json.dumps(timestamps),
        temperatures=json.dumps(temperatures),
        humidities=json.dumps(humidities)
    )
    return html

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

@app.route("/cooler_top", methods=["POST"])
def control_cooler_top():
    data = request.get_json()
    state = data.get("state")
    if state not in [True, False]:
        return jsonify({"error": "'state' must be True or False"}), 400
    cooler_top(state)
    return jsonify({
        "cooler_top": "on" if state else "off",
    })

# API to control the heater
@app.route("/heater", methods=["POST"])
def control_heater():
    data = request.get_json()
    state = data.get("state")
    if state not in [True, False]:
        return jsonify({"error": "'state' must be True or False"}), 400
    heater(state)
    auto_control_state(False) 
    return jsonify({
        "heater": "on" if state else "off",
    })

@app.route("/auto", methods=["POST"])
def auto():
    data = request.get_json()
    state = data.get("state")
    if state not in [True, False]:
        return jsonify({"error": "'state' must be True or False"}), 400
    auto_control_state(state) 
    return jsonify({
        "auto": "on" if state else "off",
    })

@app.route("/shutdown", methods=["POST"])
def shutdown():
    cleanup()


def init():
    global file_path
    if os.path.exists(file_path):
        with open(file_path, 'w') as f:
            json.dump([], f)

    status(False)
    cooler(False)
    heater(False)
    cooler_top(False)

def cleanup():
    global running, thread_obj

    print("Stopping process...")
    running = False
    status(False)
    cooler(False)
    heater(False)
    cooler_top(False)

    thread_obj.join()
    exit(0)

atexit.register(cleanup)  # Chama em encerramento normal

def handle_signal(signum, frame):
    cleanup()

signal.signal(signal.SIGINT, handle_signal)   # Ctrl+C
signal.signal(signal.SIGTERM, handle_signal)  # kill

if __name__ == "__main__":
    lib.init()
    init()

    # Start the control thread
    thread_obj = threading.Thread(target=temperature_control_loop, daemon=True)
    thread_obj.start()
    app.run(host="192.168.15.10", port=5000)
    






