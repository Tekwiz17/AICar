#pragma once

// One side's two motors each have their own L298N channel. Their input/enable
// signals are shared, not their motor outputs. IO is injectable for host tests.
namespace L298N {
constexpr unsigned REVERSAL_DEADTIME_US = 200;

// Default: a kit's normally-open pushbutton between D2 and GND.
// Optional NC contact: set STOP_CONTACT_NC=true in sketch.ino.
constexpr bool stopRequested(bool pinHigh, bool normallyClosed) {
  return normallyClosed ? pinHigh : !pinHigh;
}

template <typename IO> class Side {
 public:
  Side(int enable, int in1, int in2, bool forwardHigh = true)
      : enable_(enable), in1_(in1), in2_(in2), forwardHigh_(forwardHigh) {}

  void begin() {
    IO::output(enable_);
    IO::pwm(enable_, 0);
    IO::output(in1_);
    IO::output(in2_);
    stop();
  }

  void stop() {
    IO::pwm(enable_, 0);
    IO::digital(in1_, false);
    IO::digital(in2_, false);
    previous_ = 0;
  }

  void drive(int speed) {
    if (speed == 0 || speed < -255 || speed > 255) {
      stop();
      return;
    }
    if (previous_ != 0 && (speed > 0) != (previous_ > 0)) {
      IO::pwm(enable_, 0);
      IO::pause(REVERSAL_DEADTIME_US);
    }
    const bool in1High = (speed > 0) == forwardHigh_;
    IO::digital(in1_, in1High);
    IO::digital(in2_, !in1High);
    IO::pwm(enable_, speed < 0 ? -speed : speed);
    previous_ = speed;
  }

 private:
  int enable_, in1_, in2_;
  bool forwardHigh_;
  int previous_ = 0;
};
}  // namespace L298N
