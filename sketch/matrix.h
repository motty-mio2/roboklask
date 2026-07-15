#ifndef MATRIX_H_
#define MATRIX_H_
#include <Arduino_LED_Matrix.h>

#include <algorithm>
#include <cmath>

// Animation playback state
static const int MAX_FRAMES = 300;
static uint32_t animation_buf[MAX_FRAMES][5];  // 4 words + duration (ms)
static int animation_frame_count = 0;
static bool animation_running = false;
static int animation_current_frame = 0;
static unsigned long animation_next_time = 0;

constexpr uint8_t WIDTH = 13;
constexpr int8_t HALF_WIDTH = WIDTH / 2;
constexpr uint8_t HEIGHT = 8;

const uint8_t* generate_matrix(const float& x, const float& y) {
  static uint8_t led[104];
  memset(led, 0, sizeof(led));

  int xx = int(std::round(std::min(std::max(y, -1.0f), 1.0f) * HALF_WIDTH + HALF_WIDTH));
  int yy = int(std::round(std::min(std::max(x, 0.0f), 1.0f) * (HEIGHT - 1)));

  led[xx + yy * WIDTH] = 1;

  return led;
}

// --- Bridge providers --------------------------------------------------------

void xy(Arduino_LED_Matrix& matrix, const float& x, const float& y) {
  matrix.draw(generate_matrix(x, y));
}

#endif  // MATRIX_H_