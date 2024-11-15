#pragma once

#include "libraries/pico_display_2/pico_display_2.hpp"
#include "drivers/st7789/st7789.hpp"
#include "libraries/pico_graphics/pico_graphics.hpp"
#include "rgbled.hpp"
#include "button.hpp"

extern pimoroni::ST7789 st7789;
extern pimoroni::PicoGraphics_PenRGB332 graphics;

extern pimoroni::RGBLED led;

extern pimoroni::Button button_a;
extern pimoroni::Button button_b;
extern pimoroni::Button button_x;
extern pimoroni::Button button_y;

extern pimoroni::Pen BG;
extern pimoroni::Pen WHITE;

extern pimoroni::Point text_location;

extern std::string textToDisplay;
