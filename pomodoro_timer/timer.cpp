#include "timer.hpp"

Timer::Timer(std::function<bool()> callback, int delayInSec)
  : _callback(callback), _delayInMs(delayInSec * 1000) {}

void Timer::start() {
  sleep_ms(_delayInMs);
  _callback();
}
