#pragma once

#include <functional>
#include <atomic>
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
  int _totalTime;
  static int _remainingTime;
  repeating_timer timer;

  static bool repeatingTimerCallback(__unused struct repeating_timer *t);
};
