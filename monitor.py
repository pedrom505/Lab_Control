from flask import Flask, jsonify
import requests
import threading
import time

import matplotlib.pyplot as plt
import matplotlib.animation as animation
import requests
from datetime import datetime

app = Flask(__name__)

status_url = "http://192.168.15.10:5000/status"

# Histórico completo
timestamps = []
humidities = []
temperatures = []

fig, ax = plt.subplots()
line1, = ax.plot([], [], label="Umidade (%)", color="blue")
line2, = ax.plot([], [], label="Temperatura (°C)", color="red")

def init():
    ax.set_xlabel("Tempo")
    ax.set_ylabel("Valor")
    ax.legend()
    return line1, line2

def update(frame):
    try:
        try:
            response = requests.get(status_url, timeout=2)
            data = response.json()
        except Exception as e:
            print("Erro ao buscar dados:", e)

        now = datetime.now().strftime("%H:%M:%S")

        if data["Humidity"] is not None and data["Temperature"] is not None:
            timestamps.append(now)
            humidities.append(round(data["Humidity"], 2))
            temperatures.append(round(data["Temperature"], 2))

            line1.set_data(range(len(humidities)), humidities)
            line2.set_data(range(len(temperatures)), temperatures)

            ax.set_xlim(0, len(timestamps))
            ax.set_xticks(range(len(timestamps)))
            ax.set_xticklabels(timestamps, rotation=45, ha='right')

            min_val = min(min(humidities), min(temperatures)) - 5
            max_val = max(max(humidities), max(temperatures)) + 5
            ax.set_ylim(min_val, max_val)

            # Remove textos antigos
            [txt.remove() for txt in ax.texts]
            # Remove linhas horizontais antigas
            [line.remove() for line in ax.lines[2:]]  # Mantém apenas as duas linhas principais

            # Adiciona texto com o último valor de umidade
            ax.text(len(humidities)-1, humidities[-1], f"{humidities[-1]}%", color="blue", fontsize=9, va='bottom', ha='right')
            # Adiciona texto com o último valor de temperatura
            ax.text(len(temperatures)-1, temperatures[-1], f"{temperatures[-1]}°C", color="red", fontsize=9, va='top', ha='right')

            # Máximos e mínimos de umidade
            idx_max_h = humidities.index(max(humidities))
            idx_min_h = humidities.index(min(humidities))
            ax.text(idx_max_h, max(humidities), f"Máx: {max(humidities)}%", color="blue", fontsize=8, va='bottom', ha='left')
            ax.text(idx_min_h, min(humidities), f"Mín: {min(humidities)}%", color="blue", fontsize=8, va='top', ha='left')

            # Máximos e mínimos de temperatura
            idx_max_t = temperatures.index(max(temperatures))
            idx_min_t = temperatures.index(min(temperatures))
            ax.text(idx_max_t, max(temperatures), f"Máx: {max(temperatures)}°C", color="red", fontsize=8, va='bottom', ha='left')
            ax.text(idx_min_t, min(temperatures), f"Mín: {min(temperatures)}°C", color="red", fontsize=8, va='top', ha='left')

            last_60 = temperatures[-60:] if len(temperatures) >= 60 else temperatures
            if last_60:
                max_temp_60 = max(last_60)
                min_temp_60 = min(last_60)
                ax.axhline(max_temp_60, color='red', linestyle='--', linewidth=1, label='Temperature Máx 60')
                ax.axhline(min_temp_60, color='red', linestyle='--', linewidth=1, label='Temperature Mín 60')

            last_60 = humidities[-60:] if len(humidities) >= 60 else humidities
            if last_60:
                max_temp_60 = max(last_60)
                min_temp_60 = min(last_60)
                ax.axhline(max_temp_60, color='blue', linestyle='--', linewidth=1, label='Humidity Máx 60')
                ax.axhline(min_temp_60, color='blue', linestyle='--', linewidth=1, label='Humidity Mín 60')
    except Exception as e:
        print("Erro ao atualizar gráfico:", e)

    return line1, line2


if __name__ == "__main__":
    ani = animation.FuncAnimation(fig, update, init_func=init, interval=5000)
    plt.tight_layout()
    plt.show()