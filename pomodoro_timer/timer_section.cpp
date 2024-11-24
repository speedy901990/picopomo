#include "timer_section.hpp"

DisplaySection::DisplaySection(std::string label, int timerCountdown) : _label(label), _timer(timerCountdown) {
}

bool DisplaySection::isActive() {
  return _isActive;
}
