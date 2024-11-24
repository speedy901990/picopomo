#pragma once

#include <string>

#include "display_utils.hpp"
#include "timer.hpp"

class Section {
public:
  Section();
  
protected:
  Timer timer;
  pimoroni::Point timerPosition;
  std::string label;
  pimoroni::Point labelPosition;
};
