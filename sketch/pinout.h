#ifndef PINOUT_H
#define PINOUT_H

#include <stdint.h>

// 12V Power Sense (monitoring pin connected via voltage divider, net A0)
constexpr uint8_t V_SENSE = 2;

// Motor Driver Enable (active LOW for TMC2209)
constexpr uint8_t nEN = 3;

// TMC2209 UART Communication
constexpr uint8_t TMC_TX = 4; // MCU2TMC (connected via 1k resistor)
constexpr uint8_t TMC_RX = 5; // TMC2MCU (connected directly)

// Stepper Motor Pins (Y Axis - TMC2209 A3)
constexpr uint8_t MY_STEP = 6;
constexpr uint8_t MY_DIR = 7;
constexpr uint8_t DIAG_Y = 8;

// Stepper Motor Pins (X Axis - TMC2209 A2)
constexpr uint8_t MX_STEP = 9;
constexpr uint8_t MX_DIR = 10;
constexpr uint8_t DIAG_X = 11;

// Limit Switches (active LOW with internal pullup)
constexpr uint8_t SW_Y = 12;
constexpr uint8_t SW_X = 13;

#endif // PINOUT_H
