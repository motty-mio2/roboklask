#ifndef MATRIX_H_
#define MATRIX_H_
#include <Arduino_LED_Matrix.h>

#include <algorithm>

// Animation playback state
static const int MAX_FRAMES = 300;
static uint32_t animation_buf[MAX_FRAMES][5]; // 4 words + duration (ms)
static int animation_frame_count = 0;
static bool animation_running = false;
static int animation_current_frame = 0;
static unsigned long animation_next_time = 0;

constexpr uint8_t WIDTH = 13;
constexpr float HALF_WIDTH = WIDTH / 2.0f;
constexpr uint8_t HEIGHT = 8;

const uint8_t *generate_matrix(const float &x, const float &y) {
  static uint8_t led[WIDTH * HEIGHT];
  memset(led, 0, sizeof(led));

  // y (ボールの前後座標 -1.0 〜 1.0) をマトリクスの横方向 (0 〜 WIDTH-1) にマッピング
  int xx = (std::min(std::max(y, -1.0f), 1.0f) + 1.0f) * HALF_WIDTH;
  
  // x (ボールの左右座標 -1.0 〜 1.0) をマトリクスの縦方向 (0 〜 HEIGHT-1) にマッピング
  // x の範囲 [-1.0, 1.0] を [0.0, 1.0] に変換してから HEIGHT を掛けます
  float x_0_to_1 = (std::min(std::max(x, -1.0f), 1.0f) + 1.0f) / 2.0f;
  int yy = int(x_0_to_1 * (float)HEIGHT);

  // 境界外への書き込み（バッファオーバーフロー）を防止する安全クリップ
  xx = std::max(0, std::min(xx, (int)WIDTH - 1));
  yy = std::max(0, std::min(yy, (int)HEIGHT - 1));

  led[xx + yy * WIDTH] = 1;

  return led;
}

// --- Bridge providers --------------------------------------------------------

void xy(Arduino_LED_Matrix &matrix, const float &x, const float &y) {
  matrix.draw(generate_matrix(x, y));
}

#endif // MATRIX_H_