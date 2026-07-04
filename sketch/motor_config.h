#ifndef MOTOR_CONFIG_H
#define MOTOR_CONFIG_H_

constexpr int setM0 = false;
constexpr int setM1 = false;
constexpr int setM2 = false;

// 1回転あたりのベースステップ数
constexpr int STEP = 400;
constexpr int resolution =
    std::min(32, (setM0 ? 2 : 1) * (setM1 ? 4 : 1) * (setM2 ? 16 : 1));

// 盤面の可動最大ステップ数
constexpr int STEP_BACK = 100;
constexpr int XSTEP = 3100 - STEP_BACK * 2;
constexpr int YSTEP = 1500 - STEP_BACK;

constexpr long HOMING_CHUNK = -10;

#endif // MOTOR_CONFIG_H_