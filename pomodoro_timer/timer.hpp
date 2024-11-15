#pragma once
#include <functional>
#include "pico/stdlib.h"
#include <ctime>

class Timer
{
public:
  Timer(std::function<bool()> callback, int delayInSec);
  void start();
  
private:
  std::function<bool()> _callback;
  int _delayInMs;
};
