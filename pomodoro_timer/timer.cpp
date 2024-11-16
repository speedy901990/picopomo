#include "timer.hpp"
#include <sstream>

int Timer::_remainingTime = 0;

Timer::Timer(int countdown)
  : _totalTime(countdown) {
  //_remainingTime = countdown;
}

bool Timer::repeatingTimerCallback(__unused struct repeating_timer *t) {
  _remainingTime++;

  std::stringstream ss;
  ss << _remainingTime << "s";
  textToDisplay = ss.str();
  
  return true;
}

void Timer::start() {
  add_repeating_timer_ms(1000, repeatingTimerCallback, NULL, &timer);
}

void Timer::stop() {
  textToDisplay="STOPPED";
  cancel_repeating_timer(&timer);
}

void Timer::reset() {
  std::stringstream ss;
  ss << "Remaining: " << _remainingTime;
  textToDisplay = ss.str();
}
