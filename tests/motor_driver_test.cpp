#include <cassert>
#include <tuple>
#include <vector>
#include "../sketch/L298N.h"

using Event = std::tuple<char, int, int>;
struct FakeIO {
  static std::vector<Event> events;
  static void output(int p) { events.emplace_back('o', p, 0); }
  static void digital(int p, bool v) { events.emplace_back('d', p, v); }
  static void pwm(int p, int v) { events.emplace_back('p', p, v); }
  static void pause(unsigned us) { events.emplace_back('t', 0, us); }
};
std::vector<Event> FakeIO::events;

int main() {
  L298N::Side<FakeIO> side(6, 8, 9);
  side.begin();
  assert(FakeIO::events.at(1) == Event('p', 6, 0));
  assert(FakeIO::events.back() == Event('d', 9, 0));
  FakeIO::events.clear();
  side.drive(85);
  assert((FakeIO::events == std::vector<Event>{{'d',8,1},{'d',9,0},{'p',6,85}}));
  FakeIO::events.clear();
  side.drive(-70);
  assert((FakeIO::events == std::vector<Event>{{'p',6,0},{'t',0,200},
      {'d',8,0},{'d',9,1},{'p',6,70}}));
  FakeIO::events.clear();
  side.drive(-60);  // Same direction: no dead time or interruption.
  assert((FakeIO::events == std::vector<Event>{{'d',8,0},{'d',9,1},{'p',6,60}}));
  FakeIO::events.clear();
  side.drive(0);  // Disable first, then neutral direction inputs.
  assert((FakeIO::events == std::vector<Event>{{'p',6,0},{'d',8,0},{'d',9,0}}));
  FakeIO::events.clear();
  side.drive(256);
  assert(FakeIO::events.front() == Event('p',6,0));
  L298N::Side<FakeIO> reversed(5, 7, 4, false);
  FakeIO::events.clear();
  reversed.drive(70);
  assert((FakeIO::events == std::vector<Event>{{'d',7,0},{'d',4,1},{'p',5,70}}));
  assert(L298N::stopRequested(false, false));  // Pressed kit button.
  assert(!L298N::stopRequested(true, false));  // Released kit button.
  assert(L298N::stopRequested(true, true));   // Open optional NC contact.
  assert(!L298N::stopRequested(false, true));
}
