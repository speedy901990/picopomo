#include "timer.hpp"
extern std::string textToDisplay;

Timer::Timer(int countdown)
  : _totalCountdown(countdown), _remainingCountdown(countdown) {
}

bool Timer::repeatingTimerCallback(__unused struct repeating_timer *t) {
  textToDisplay="COUNTDOWN DONE";
  return true;
}

void Timer::start() {
  add_repeating_timer_ms(5000, repeatingTimerCallback, NULL, &timer);
  //sleep_ms(2000);
}

void Timer::stop() {
  textToDisplay="STOPPED";
  cancel_repeating_timer(&timer);
}

void Timer::reset() {
  
}
