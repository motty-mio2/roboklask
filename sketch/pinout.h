#ifndef PINOUT_H
#define PINOUT_H

constexpr uint8_t M0 = 0;
constexpr uint8_t M1 = 1;
constexpr uint8_t M2 = 2;
constexpr uint8_t nEN = 3;
constexpr uint8_t MY_STEP = 4;
constexpr uint8_t MY_DIR = 5;
constexpr uint8_t MX_STEP = 8;
constexpr uint8_t MX_DIR = 9;
constexpr uint8_t VEN = 10;

constexpr uint8_t SW_A = 12;
constexpr uint8_t SW_B = 13;

// Uno R4
#if defined(ARDUINO_MINIMA)
#pragma message "\n >> ARDUINO_MINIMA is defined."
constexpr uint8_t SW_X = 19;
constexpr uint8_t SW_Y = 18;
#elif defined(ARDUINO_UNO_Q)
#pragma message "\n >> ARDUINO_UNO_Q is defined."
constexpr uint8_t SW_X = 21;
constexpr uint8_t SW_Y = 20;
#endif

#endif  // PINOUT_H