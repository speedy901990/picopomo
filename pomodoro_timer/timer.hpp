#pragma once

#include <functional>
#include "pico/stdlib.h"
#include "display_utils.hpp"

class Timer
{
public:
  Timer(int countdown);
  void start();
  void stop();
  void reset();
  bool isRunning();
  
private:
  int _totalCountdown;
  int _remainingCountdown;
  struct repeating_timer timer;

  static bool repeatingTimerCallback(__unused struct repeating_timer *t);
};
