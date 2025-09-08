#include <wiringPi.h>
#include <iostream>
#include <cstdlib>
#include <stdint.h>
#include <unistd.h>
#include "dht22.h"
using namespace std;

#define MAX_TIMINGS 85

float humidity;
float temperature;

void init(){
    wiringPiSetup();
}

void READ_DHT22(int DHT22_PIN) {

    int data[5] = {0, 0, 0, 0, 0};

    uint8_t lastState = HIGH;
    uint8_t counter = 0;
    uint8_t j = 0, i;
    bool valid = false;
    float local_humidity;
    float local_temperature;

    while (!valid){
        lastState = HIGH;
        j = i = counter = 0;
        data[0] = data[1] = data[2] = data[3] = data[4] = 0;

        pinMode(DHT22_PIN, OUTPUT);
        digitalWrite(DHT22_PIN, LOW);
        delay(18);
        digitalWrite(DHT22_PIN, HIGH);
        delayMicroseconds(40);
        pinMode(DHT22_PIN, INPUT);

        for (i = 0; i < MAX_TIMINGS; i++) {
            counter = 0;
            while (digitalRead(DHT22_PIN) == lastState) {
                counter++;
                delayMicroseconds(1);
                if (counter == 255) break;
            }

            lastState = digitalRead(DHT22_PIN);

            if (counter == 255) break;

            if ((i >= 4) && (i % 2 == 0)) {
                data[j / 8] <<= 1;
                if (counter > 16) data[j / 8] |= 1;
                j++;
            }
        }

        if (j >= 40 &&
            data[4] == ((data[0] + data[1] + data[2] + data[3]) & 0xFF)) {
            local_humidity = ((data[0] << 8) + data[1]) * 0.1;
            local_temperature = (((data[2] & 0x7F) << 8) + data[3]) * 0.1;
            if (data[2] & 0x80) local_temperature = -local_temperature;
            

            if (local_temperature == 0 || local_humidity == 0 || local_temperature < 0 || local_humidity < 0){
                cout << "Temperature: " << local_temperature << "/ Humidity: " << local_humidity << endl;
                delay(1000);
                valid = false;
            } else {
                temperature = local_temperature; 
                humidity = local_humidity;

                valid = true;
            }
        }
    }
}

float GET_TEMPERATURE(){
    return temperature;
}

float GET_HUMIDITY(){
    return humidity;
}

void GPIO_OUT(int LED_PIN, int LEVEL) {
    pinMode(LED_PIN, OUTPUT);
    if(LEVEL > 0)
        digitalWrite(LED_PIN, HIGH);
    else
        digitalWrite(LED_PIN, LOW);
}