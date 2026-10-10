#include <cassert>
#include "../sketch/Safety.h"
int main() {
  using Safety::motionAllowed;
  assert(motionAllowed(true,false,50,1000,20,90,500,80,80));
  assert(!motionAllowed(false,false,50,1000,20,90,500,80,80));
  assert(!motionAllowed(true,true,50,1000,20,90,500,80,80));
  assert(!motionAllowed(true,false,501,1000,20,90,500,80,80));
  assert(!motionAllowed(true,false,50,-1,20,90,500,80,80));
  assert(!motionAllowed(true,false,50,1000,251,90,500,80,80));
  assert(!motionAllowed(true,false,50,300,20,90,500,80,80));
  assert(!motionAllowed(true,false,50,1000,20,125,500,80,80));
  assert(!motionAllowed(true,false,50,1000,20,90,399,80,80));
  assert(!motionAllowed(true,false,50,1000,20,90,500,-80,-80));
  assert(!motionAllowed(true,false,50,1000,20,90,500,255,255));
  assert(motionAllowed(true,false,50,250,20,90,500,-70,70));
  assert(!motionAllowed(true,false,50,180,20,90,500,-70,70));
  assert(!motionAllowed(true,false,501,1000,20,90,500,-70,70));
}
