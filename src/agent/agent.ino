#include <dht.h>
#include <LiquidCrystal.h>
#include <Servo.h>
#include "pitches.h"

// ============================================================
// Pin definitions and component setup
// ============================================================

#define DHT11_PIN 2
#define LED_PIN 13
#define BUZZER_PIN 7
#define SERVO_PIN 8

const int trigPin = 9;
const int echoPin = 10;
const int rs = 12, en = 11, d4 = 6, d5 = 5, d6 = 4, d7 = 3;

dht DHT;
Servo myservo;
LiquidCrystal lcd(rs, en, d4, d5, d6, d7);

// Melody for buzzer
int melody[] = {NOTE_C4, NOTE_G3, NOTE_G3, NOTE_A3, NOTE_G3, 0, NOTE_B3, NOTE_C4};
int noteDurations[] = {4, 8, 8, 4, 4, 4, 4, 4};

// ============================================================
// Setup
// ============================================================

void setup() {
  Serial.begin(9600);
  
  pinMode(LED_PIN, OUTPUT);
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);
  
  myservo.attach(SERVO_PIN);
  myservo.write(90);  // Centre position at start
  
  lcd.begin(16, 2);
  lcd.print("Agent ready");
  
  digitalWrite(LED_PIN, LOW);
  
  Serial.println("READY");
}

// ============================================================
// Component functions - one for each capability
// ============================================================

float readTemperature() {
  int chk = DHT.read11(DHT11_PIN);
  if (chk != DHTLIB_OK) return -999.0;
  return DHT.temperature;
}

float readHumidity() {
  int chk = DHT.read11(DHT11_PIN);
  if (chk != DHTLIB_OK) return -999.0;
  return DHT.humidity;
}

long readDistance() {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);
  
  long duration = pulseIn(echoPin, HIGH, 30000);  // 30ms timeout
  if (duration == 0) return -1;
  
  long distance = (duration * 0.0343) / 2;
  return distance;
}

void setServoAngle(int angle) {
  angle = constrain(angle, 0, 180);
  myservo.write(angle);
}

void setLed(bool state) {
  digitalWrite(LED_PIN, state ? HIGH : LOW);
}

void playBuzzerSimple(int duration_ms) {
  duration_ms = constrain(duration_ms, 100, 5000);
  tone(BUZZER_PIN, 1000);  // Simple 1kHz tone
  delay(duration_ms);
  noTone(BUZZER_PIN);
}

void playBuzzerMelody() {
  for (int thisNote = 0; thisNote < 8; thisNote++) {
    int noteDuration = 1000 / noteDurations[thisNote];
    tone(BUZZER_PIN, melody[thisNote], noteDuration);
    int pauseBetweenNotes = noteDuration * 1.30;
    delay(pauseBetweenNotes);
    noTone(BUZZER_PIN);
  }
}

void displayOnLcd(String text) {
  lcd.clear();
  
  if (text.length() <= 16) {
    lcd.setCursor(0, 0);
    lcd.print(text);
  } else {
    // Split across two lines
    lcd.setCursor(0, 0);
    lcd.print(text.substring(0, 16));
    lcd.setCursor(0, 1);
    int endIdx = min((int)text.length(), 32);
    lcd.print(text.substring(16, endIdx));
  }
}

// ============================================================
// Command parser - this is what the Python agent talks to
// ============================================================

void processCommand(String command) {
  command.trim();
  
  if (command == "READ_TEMP") {
    float temp = readTemperature();
    if (temp == -999.0) {
      Serial.println("ERROR");
    } else {
      Serial.println(temp, 1);
    }
  }
  
  else if (command == "READ_HUMIDITY") {
    float h = readHumidity();
    if (h == -999.0) {
      Serial.println("ERROR");
    } else {
      Serial.println(h, 1);
    }
  }
  
  else if (command == "READ_DIST") {
    long dist = readDistance();
    if (dist == -1) {
      Serial.println("OUT_OF_RANGE");
    } else {
      Serial.println(dist);
    }
  }
  
  else if (command.startsWith("SERVO:")) {
    int angle = command.substring(6).toInt();
    setServoAngle(angle);
    Serial.println("OK");
  }
  
  else if (command == "LED:ON") {
    setLed(true);
    Serial.println("OK");
  }
  
  else if (command == "LED:OFF") {
    setLed(false);
    Serial.println("OK");
  }
  
  else if (command.startsWith("BUZZER:")) {
    int duration = command.substring(7).toInt();
    playBuzzerSimple(duration);
    Serial.println("OK");
  }
  
  else if (command == "BUZZER_MELODY") {
    playBuzzerMelody();
    Serial.println("OK");
  }
  
  else if (command.startsWith("LCD:")) {
    String text = command.substring(4);
    displayOnLcd(text);
    Serial.println("OK");
  }
  
  else {
    Serial.println("UNKNOWN_COMMAND");
  }
}

// ============================================================
// Main loop - just listens for commands
// ============================================================

void loop() {
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    processCommand(command);
  }
}
