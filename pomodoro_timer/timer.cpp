#include "timer.hpp"
#include <sstream>

std::atomic<bool> Timer::_running = false;

Timer::Timer(int countdown)
  : _totalTime(countdown * 1000), _remainingTime(countdown * 1000) {
}

int64_t Timer::alarm_callback(alarm_id_t id, __unused void *user_data) {
  //textToDisplay = "DONE";
  _running = false;
  return 0;
}

void Timer::start() {
  if (isRunning()) {
    return;
  }
  
  _alarmId = add_alarm_in_ms(_remainingTime, alarm_callback, NULL, false);
  _running = true;
}

void Timer::pause() {
  _remainingTime = remaining_alarm_time_ms(_alarmId);
  std::stringstream ss;
  ss << "PAUSED remaining: " << getRemainingTime() << " s";
  ss << " | is running: " << _running;
  textToDisplay = ss.str();
  _running = false;
}

void Timer::stop() {
  textToDisplay="STOPPED";
  _running = !cancel_alarm(_alarmId);
  _remainingTime = _totalTime;
  _running = false;
}

void Timer::reset() {
  bool wasRunning = isRunning();
  stop();
  if (wasRunning) {
    start();
  }
}

bool Timer::isRunning() {
  return _running;
}

int Timer::getRemainingTime() {
  return remaining_alarm_time_ms(_alarmId) / 1000;
}
