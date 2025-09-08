// dht22.h
extern "C" {
    void init();
    void READ_DHT22(int DHT22_PIN);
    float GET_TEMPERATURE();
    float GET_HUMIDITY();
    void GPIO_OUT(int LED_PIN, int LEVEL);
}