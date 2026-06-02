#include <Arduino_LED_Matrix.h>
#include <Arduino_RouterBridge.h>
#include <zephyr/kernel.h>

#include <vector>

Arduino_LED_Matrix matrix;

// Bridge providers run on a separate thread from loop().
// This mutex protects shared animation state and serializes LED matrix writes.
K_MUTEX_DEFINE(anim_mtx);

// Animation playback state
static const int MAX_FRAMES = 300;
static uint32_t animation_buf[MAX_FRAMES][5];  // 4 words + duration (ms)
static int animation_frame_count = 0;
static bool animation_running = false;
static int animation_current_frame = 0;
static unsigned long animation_next_time = 0;

constexpr uint8_t WIDTH = 13;
constexpr uint8_t HALF_WIDTH = WIDTH / 2;
constexpr uint8_t HEIGHT = 8;

void setup() {
  matrix.begin();
  matrix.setGrayscaleBits(1);
  matrix.clear();

  Bridge.begin();
  Bridge.provide("xy", xy);

  Monitor.begin();
}

void loop() { delay(1); }

// --- Functions

uint8_t* generate_matrix(float x, float y) {
  static uint8_t led[HEIGHT][WIDTH];
  memset(led, 0, sizeof(led));

  int xx = int(min(max(y, -1.0f), 1.0f) * HALF_WIDTH + HALF_WIDTH);
  int yy = int(min(max(x, 0.0f), 1.0f) * (HEIGHT - 1));

  led[yy][xx] = 1;

  return (uint8_t*)led;
}

// --- Bridge providers --------------------------------------------------------

void xy(float x, float y) {
  Monitor.print("Setting pixel at (");
  Monitor.print(x);
  Monitor.print(", ");
  Monitor.print(y);
  Monitor.println(") to max brightness");

  matrix.draw(generate_matrix(x, y));
}
