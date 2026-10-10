#pragma once
#include <stdint.h>

// Pure policy, also exercised by the host C++ tests.
namespace Safety {
constexpr uint32_t COMMAND_TIMEOUT_MS = 500;
constexpr uint32_t RANGE_TIMEOUT_MS = 250;
constexpr uint32_t SETTLE_MS = 400;
constexpr int FORWARD_MIN_MM = 300;
constexpr int PIVOT_MIN_MM = 180;
constexpr int MAX_PWM = 110;

inline bool motionAllowed(bool armed, bool estop, uint32_t commandAge,
                          int distanceMm, uint32_t rangeAge, int pan,
                          uint32_t settledMs, int left, int right) {
  if (!armed || estop || commandAge > COMMAND_TIMEOUT_MS) return false;
  if (left == 0 && right == 0) return true;
  if (left < -MAX_PWM || left > MAX_PWM || right < -MAX_PWM || right > MAX_PWM) return false;
  // Never reverse the chassis into an unobserved rear obstacle.
  if (left < 0 && right < 0) return false;
  if (pan < 87 || pan > 93 || settledMs < SETTLE_MS) return false;
  if (distanceMm <= 0 || rangeAge > RANGE_TIMEOUT_MS) return false;
  bool pivot = (left < 0 && right > 0) || (right < 0 && left > 0);
  return distanceMm > (pivot ? PIVOT_MIN_MM : FORWARD_MIN_MM);
}
}
