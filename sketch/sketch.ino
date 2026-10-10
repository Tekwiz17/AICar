/* AICar: UNO Q only, two L298N modules, four original ELEGOO motors.
 * New implementation; see docs/UPSTREAM.md for reference provenance.
 */
#include <Arduino.h>
#include <Arduino_RouterBridge.h>
#include <Arduino_HardwareServo.h>
#include <zephyr/kernel.h>
#include "Safety.h"
#include "L298N.h"

constexpr int PWM_RIGHT = D5, PWM_LEFT = D6;
constexpr int RIGHT_IN1 = D7, RIGHT_IN2 = D4, LEFT_IN1 = D8, LEFT_IN2 = D9;
constexpr int PAN = D10, TRIG = D13, ECHO = D12, ESTOP = D2;
constexpr bool STOP_CONTACT_NC = false;
// Default kit button: pressing closes D2 to GND. Release never rearms.
constexpr bool LEFT_FORWARD_HIGH = true, RIGHT_FORWARD_HIGH = true;
struct MotorIO {
  static void output(int pin) { pinMode(pin, OUTPUT); }
  static void digital(int pin, bool high) { digitalWrite(pin, high ? HIGH : LOW); }
  static void pwm(int pin, int value) { analogWrite(pin, value); }
  static void pause(unsigned us) { delayMicroseconds(us); }
};
L298N::Side<MotorIO> leftMotor(PWM_LEFT, LEFT_IN1, LEFT_IN2, LEFT_FORWARD_HIGH);
L298N::Side<MotorIO> rightMotor(PWM_RIGHT, RIGHT_IN1, RIGHT_IN2, RIGHT_FORWARD_HIGH);
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
  rightMotor.stop();
  leftMotor.stop();
}

bool physicalStopPressed() {
  return L298N::stopRequested(digitalRead(ESTOP) == HIGH, STOP_CONTACT_NC);
}

bool stop_car() {
  k_mutex_lock(&stateMutex, K_FOREVER);
  state.armed = false;
  state.left = state.right = 0;
  state.fault = "stopped";
  motorStop();
  k_mutex_unlock(&stateMutex);
  return true;
}

bool arm_car() {
  k_mutex_lock(&stateMutex, K_FOREVER);
  bool ok = !physicalStopPressed() && state.servoOK;
  state.armed = ok;
  state.left = state.right = 0;
  motorStop();
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
    motorStop();
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
  // External enable pull-downs keep all four channels off before setup runs.
  leftMotor.begin();
  rightMotor.begin();
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
  state.estop = physicalStopPressed();
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
    // Driver drops PWM and inserts dead time before a powered direction reversal.
    leftMotor.drive(state.left);
    rightMotor.drive(state.right);
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
