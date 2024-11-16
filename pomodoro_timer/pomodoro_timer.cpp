#include <math.h>
#include <cstdlib>
#include <sstream>

#include "pico/stdlib.h"
#include "timer.hpp"
#include "display_utils.hpp"


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
