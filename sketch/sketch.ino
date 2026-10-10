/* AICar: UNO Q only. ELEGOO V4 pin map / direction convention preserved.
 * New implementation; see docs/UPSTREAM.md for reference provenance.
 */
#include <Arduino.h>
#include <Arduino_RouterBridge.h>
#include <Arduino_HardwareServo.h>
#include <zephyr/kernel.h>
#include "Safety.h"

constexpr int PWM_RIGHT = D5, PWM_LEFT = D6, DIR_RIGHT = D7, DIR_LEFT = D8;
constexpr int STBY = D3, PAN = D10, TRIG = D13, ECHO = D12, ESTOP = D2;
// NC emergency switch: D2 to GND when released; HIGH means pressed/unplugged.
constexpr bool LEFT_FORWARD_HIGH = true, RIGHT_FORWARD_HIGH = true;
K_MUTEX_DEFINE(stateMutex);
HardwareServo panServo;
struct Shared {
  int left = 0, right = 0, requestedPan = 90;
  int actualPan = 90, distance = -1;
  bool armed = false, estop = true, servoOK = false;
  uint32_t commandAt = 0, rangeAt = 0, panAt = 0;
  const char *fault = "boot";
} state;

void motorStop() {
  analogWrite(PWM_RIGHT, 0);
  analogWrite(PWM_LEFT, 0);
  digitalWrite(STBY, LOW);
}

bool stop_car() {
  k_mutex_lock(&stateMutex, K_FOREVER);
  state.armed = false;
  state.left = state.right = 0;
  state.fault = "stopped";
  k_mutex_unlock(&stateMutex);
  return true;
}

bool arm_car() {
  k_mutex_lock(&stateMutex, K_FOREVER);
  bool ok = digitalRead(ESTOP) == LOW && state.servoOK;
  state.armed = ok;
  state.left = state.right = 0;
  state.commandAt = millis();
  state.fault = ok ? "armed" : "estop_or_servo";
  k_mutex_unlock(&stateMutex);
  return ok;
}

bool drive_car(int left, int right, int pan) {
  k_mutex_lock(&stateMutex, K_FOREVER);
  bool valid = left >= -Safety::MAX_PWM && left <= Safety::MAX_PWM &&
               right >= -Safety::MAX_PWM && right <= Safety::MAX_PWM &&
               !(left < 0 && right < 0) && pan >= 55 && pan <= 125;
  if (valid) {
    state.left = left;
    state.right = right;
    state.requestedPan = pan;
    state.commandAt = millis();
  } else {
    state.armed = false;
    state.left = state.right = 0;
    state.fault = "invalid_command";
  }
  k_mutex_unlock(&stateMutex);
  return valid;
}

String car_status() {
  k_mutex_lock(&stateMutex, K_FOREVER);
  uint32_t now = millis();
  String s = "{\"distance_mm\":" + String(state.distance) +
    ",\"sample_age_ms\":" + String(now - state.rangeAt) +
    ",\"pan\":" + String(state.actualPan) +
    ",\"settled_ms\":" + String(now - state.panAt) +
    ",\"estop\":" + String(state.estop ? "true" : "false") +
    ",\"armed\":" + String(state.armed ? "true" : "false") +
    ",\"fault\":\"" + String(state.fault) + "\"}";
  k_mutex_unlock(&stateMutex);
  return s;
}

void setup() {
  pinMode(STBY, OUTPUT);
  digitalWrite(STBY, LOW);
  pinMode(PWM_RIGHT, OUTPUT); pinMode(PWM_LEFT, OUTPUT);
  pinMode(DIR_RIGHT, OUTPUT); pinMode(DIR_LEFT, OUTPUT);
  motorStop();
  pinMode(ESTOP, INPUT_PULLUP);
  pinMode(TRIG, OUTPUT); digitalWrite(TRIG, LOW);
  pinMode(ECHO, INPUT);  // 5 V echo MUST pass through the divider in the wiring guide.
  state.servoOK = panServo.attach(PAN, 1000, 2000) != INVALID_SERVO;
  panServo.write(90);
  state.panAt = millis();
  if (!Bridge.begin()) return;  // Remains disarmed.
  Bridge.provide("arm_car", arm_car);
  Bridge.provide("stop_car", stop_car);
  Bridge.provide("drive_car", drive_car);
  Bridge.provide("car_status", car_status);
}

void loop() {
  static uint32_t lastPing = 0;
  k_mutex_lock(&stateMutex, K_FOREVER);
  uint32_t now = millis();
  state.estop = digitalRead(ESTOP) != LOW;
  if (state.estop || (state.armed && now - state.commandAt > Safety::COMMAND_TIMEOUT_MS)) {
    state.armed = false;
    state.left = state.right = 0;
    state.fault = state.estop ? "estop" : "command_timeout";
  }
  if (state.actualPan != state.requestedPan) {
    motorStop();
    state.actualPan = state.requestedPan;
    state.panAt = now;
    state.distance = -1;  // A range taken at a previous angle is never reused.
    panServo.write(state.actualPan);
  }
  bool allowed = Safety::motionAllowed(state.armed, state.estop,
    now - state.commandAt, state.distance, now - state.rangeAt,
    state.actualPan, now - state.panAt, state.left, state.right);
  if (allowed && (state.left || state.right)) {
    // Drop PWM before direction changes to avoid instant powered reversal.
    static int previousLeft = 0, previousRight = 0;
    if ((state.left > 0) != (previousLeft > 0) ||
        (state.right > 0) != (previousRight > 0)) motorStop();
    digitalWrite(DIR_LEFT, (state.left >= 0) == LEFT_FORWARD_HIGH ? HIGH : LOW);
    digitalWrite(DIR_RIGHT, (state.right >= 0) == RIGHT_FORWARD_HIGH ? HIGH : LOW);
    digitalWrite(STBY, HIGH);
    analogWrite(PWM_LEFT, abs(state.left));
    analogWrite(PWM_RIGHT, abs(state.right));
    previousLeft = state.left; previousRight = state.right;
    state.fault = "running";
  } else {
    motorStop();
    if (state.armed) state.fault = "holding";
  }
  bool ping = now - lastPing >= 70 && now - state.panAt >= Safety::SETTLE_MS;
  int samplePan = state.actualPan;
  k_mutex_unlock(&stateMutex);
  if (ping) {
    lastPing = now;
    digitalWrite(TRIG, LOW); delayMicroseconds(2);
    digitalWrite(TRIG, HIGH); delayMicroseconds(10); digitalWrite(TRIG, LOW);
    unsigned long us = pulseIn(ECHO, HIGH, 25000UL);  // Bounded; watchdog resumes after <=25 ms.
    int mm = us > 0 ? static_cast<int>(us * 0.1715f) : -1;
    if (mm < 20 || mm > 4000) mm = -1;
    k_mutex_lock(&stateMutex, K_FOREVER);
    if (state.actualPan == samplePan) {
      state.distance = mm;
      state.rangeAt = millis();
    }
    k_mutex_unlock(&stateMutex);
  }
  delay(5);
}
