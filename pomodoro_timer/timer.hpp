#pragma once

#include <atomic>
#include "pico/stdlib.h"
#include "display_utils.hpp"

class Timer
{
public:
  Timer(int countdown);
  void start();
  void stop();
  void pause();
  void reset();
  bool isRunning();
  bool isFinished();
  int getRemainingTime();
  
private:
  int _totalTime;
  int _remainingTime;
  alarm_id_t _alarmId;

  static std::atomic<bool> _running;
  static std::atomic<bool> _finished;

  static int64_t alarm_callback(alarm_id_t id, __unused void *user_data);
};
