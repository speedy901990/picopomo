#pragma once

#include <string>

#include "display_utils.hpp"
#include "timer.hpp"

class DisplaySection {
public:
  DisplaySection(std::string label, int timeCountdown);
  bool isActive();
  
protected:
  std::string _label;
  Timer _timer;
  pimoroni::Point _timerPosition;
  pimoroni::Point _labelPosition;
  bool _isActive;
};
