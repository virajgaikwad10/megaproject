/*
  IR line crossing module for the Smart Traffic Violation Detection system.

  Wiring:
  - IR sensor VCC -> Arduino/ESP32 5V or 3.3V according to sensor rating
  - IR sensor GND -> GND
  - IR sensor OUT -> digital pin 2

  The backend reads serial text. Send "1" when the line is crossed and "0" otherwise.
*/

const int IR_SENSOR_PIN = 2;

void setup() {
  Serial.begin(9600);
  pinMode(IR_SENSOR_PIN, INPUT);
}

void loop() {
  int sensorValue = digitalRead(IR_SENSOR_PIN);

  if (sensorValue == LOW) {
    Serial.println("1");
  } else {
    Serial.println("0");
  }

  delay(100);
}
