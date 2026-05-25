#include <Servo.h>

/*
  CHEVEL AI - Arduino Mega 2560 5DOF Servo Bridge

  Serial protocol at 115200 baud:
    PING                  -> OK CHEVEL_SERVO_BRIDGE
    STATUS                -> OK STATUS a0,a1,a2,a3,a4
    HOME                  -> OK HOME
    ARM                   -> OK ARMED
    STOP                  -> OK STOPPED
    SET,index,angle       -> OK SET,index,angle
    MOVE,a0,a1,a2,a3,a4   -> OK MOVE

  Suggested hardware:
    Servo 0 base     MG996R on pin 2
    Servo 1 shoulder MG996R on pin 3
    Servo 2 elbow    MG996R on pin 4
    Servo 3 wrist    SG90   on pin 5
    Servo 4 gripper  SG90   on pin 6

  Power note:
    Do not power MG996R servos from the Arduino 5V pin. Use an external
    regulated supply with common ground.
*/

const byte SERVO_COUNT = 5;
const byte SERVO_PINS[SERVO_COUNT] = {2, 3, 4, 5, 6};

const int MIN_ANGLE[SERVO_COUNT] = {0, 15, 10, 0, 20};
const int MAX_ANGLE[SERVO_COUNT] = {180, 165, 170, 180, 160};
const int HOME_ANGLE[SERVO_COUNT] = {90, 90, 90, 90, 90};

Servo servos[SERVO_COUNT];
int currentAngle[SERVO_COUNT] = {90, 90, 90, 90, 90};
bool armed = true;

String inputLine = "";

void setup() {
  Serial.begin(115200);
  inputLine.reserve(96);
  attachServos();
  moveSmooth(HOME_ANGLE);
  Serial.println("OK CHEVEL_SERVO_BRIDGE");
}

void loop() {
  while (Serial.available() > 0) {
    char c = (char)Serial.read();
    if (c == '\n' || c == '\r') {
      if (inputLine.length() > 0) {
        handleCommand(inputLine);
        inputLine = "";
      }
    } else {
      inputLine += c;
      if (inputLine.length() > 95) {
        inputLine = "";
        Serial.println("ERR line_too_long");
      }
    }
  }
}

void attachServos() {
  for (byte i = 0; i < SERVO_COUNT; i++) {
    if (!servos[i].attached()) {
      servos[i].attach(SERVO_PINS[i]);
    }
  }
  armed = true;
}

void detachServos() {
  for (byte i = 0; i < SERVO_COUNT; i++) {
    if (servos[i].attached()) {
      servos[i].detach();
    }
  }
  armed = false;
}

void handleCommand(String raw) {
  raw.trim();
  raw.replace("<", "");
  raw.replace(">", "");

  if (raw == "PING") {
    Serial.println("OK CHEVEL_SERVO_BRIDGE");
    return;
  }
  if (raw == "STATUS") {
    printStatus();
    return;
  }
  if (raw == "ARM") {
    attachServos();
    Serial.println("OK ARMED");
    return;
  }
  if (raw == "STOP") {
    detachServos();
    Serial.println("OK STOPPED");
    return;
  }
  if (raw == "HOME") {
    if (!ensureArmed()) return;
    moveSmooth(HOME_ANGLE);
    Serial.println("OK HOME");
    return;
  }
  if (raw.startsWith("SET,")) {
    if (!ensureArmed()) return;
    handleSet(raw);
    return;
  }
  if (raw.startsWith("MOVE,")) {
    if (!ensureArmed()) return;
    handleMove(raw);
    return;
  }

  Serial.println("ERR unknown_command");
}

bool ensureArmed() {
  if (!armed) {
    Serial.println("ERR stopped_use_ARM");
    return false;
  }
  return true;
}

bool validateAngle(byte index, int angle) {
  if (index >= SERVO_COUNT) {
    Serial.println("ERR invalid_servo_index");
    return false;
  }
  if (angle < MIN_ANGLE[index] || angle > MAX_ANGLE[index]) {
    Serial.print("ERR angle_limit servo=");
    Serial.print(index);
    Serial.print(" angle=");
    Serial.println(angle);
    return false;
  }
  return true;
}

void handleSet(String raw) {
  int first = raw.indexOf(',');
  int second = raw.indexOf(',', first + 1);
  if (first < 0 || second < 0) {
    Serial.println("ERR bad_SET");
    return;
  }

  int index = raw.substring(first + 1, second).toInt();
  int angle = raw.substring(second + 1).toInt();
  if (!validateAngle(index, angle)) return;

  int target[SERVO_COUNT];
  for (byte i = 0; i < SERVO_COUNT; i++) {
    target[i] = currentAngle[i];
  }
  target[index] = angle;
  moveSmooth(target);
  Serial.print("OK SET,");
  Serial.print(index);
  Serial.print(",");
  Serial.println(angle);
}

void handleMove(String raw) {
  int target[SERVO_COUNT];
  int start = raw.indexOf(',') + 1;

  for (byte i = 0; i < SERVO_COUNT; i++) {
    int end = raw.indexOf(',', start);
    String part = end >= 0 ? raw.substring(start, end) : raw.substring(start);
    part.trim();
    if (part.length() == 0) {
      Serial.println("ERR bad_MOVE");
      return;
    }
    target[i] = part.toInt();
    if (!validateAngle(i, target[i])) return;
    start = end + 1;
    if (end < 0 && i < SERVO_COUNT - 1) {
      Serial.println("ERR MOVE_requires_5_angles");
      return;
    }
  }

  moveSmooth(target);
  Serial.println("OK MOVE");
}

void moveSmooth(const int target[SERVO_COUNT]) {
  bool moving = true;
  while (moving) {
    moving = false;
    for (byte i = 0; i < SERVO_COUNT; i++) {
      if (currentAngle[i] < target[i]) {
        currentAngle[i]++;
        moving = true;
      } else if (currentAngle[i] > target[i]) {
        currentAngle[i]--;
        moving = true;
      }
      servos[i].write(currentAngle[i]);
    }
    delay(12);
  }
}

void printStatus() {
  Serial.print("OK STATUS ");
  for (byte i = 0; i < SERVO_COUNT; i++) {
    if (i > 0) Serial.print(",");
    Serial.print(currentAngle[i]);
  }
  Serial.println();
}
