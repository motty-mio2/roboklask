#ifndef MATRIX_H_
#define MATRIX_H_

// Animation playback state
static const int MAX_FRAMES = 300;
static uint32_t animation_buf[MAX_FRAMES][5]; // 4 words + duration (ms)
static int animation_frame_count = 0;
static bool animation_running = false;
static int animation_current_frame = 0;
static unsigned long animation_next_time = 0;

constexpr uint8_t WIDTH = 13;
constexpr uint8_t HALF_WIDTH = WIDTH / 2;
constexpr uint8_t HEIGHT = 8;

#endif // MATRIX_H_