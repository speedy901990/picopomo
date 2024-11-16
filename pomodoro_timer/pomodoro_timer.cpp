#include <string.h>
#include <math.h>
#include <cstdlib>
#include "pico/stdlib.h"
#include "timer.hpp"
#include "display_utils.hpp"
#include <sstream>

using namespace pimoroni;

int main() {
  st7789.set_backlight(255);
  Timer timer(10);
  timer.start();
  
  while(true) {
    if(button_a.raw()) timer.reset();
    if(button_b.raw()) timer.stop();

    if(button_x.raw()) timer.pause();
    if(button_y.raw()) timer.start();
  
    graphics.set_pen(BG);
    graphics.clear();

    // Since HSV takes a float from 0.0 to 1.0 indicating hue,
    // then we can divide millis by the number of milliseconds
    // we want a full colour cycle to take. 5000 = 5 sec
    //RGB p = RGB::from_hsv((float)millis() / 5000.0f, 1.0f, 0.5f + sinf(millis() / 100.0f / 3.14159f) * 0.5f);
    RGB p = RGB::from_hsv(0,0,0);
    led.set_rgb(p.r, p.g, p.b);

    if (timer.isRunning()) {
      std::stringstream ss;
      ss << "Timer Remaining: " << timer.getRemainingTime() << "s";
      textToDisplay = ss.str();
    }

     graphics.set_pen(WHITE);
     graphics.text(textToDisplay, text_location, 320);
    
    // update screen
     st7789.update(&graphics);
  }

    return 0;
}
