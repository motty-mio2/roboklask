#ifndef MOTOR_CONFIG_H
#define MOTOR_CONFIG_H_

constexpr int setM0 = true;
constexpr int setM1 = true;
constexpr int setM2 = false;

// 1回転あたりのベースステップ数
constexpr int STEP = 400;
constexpr int resolution = 8;

// 盤面の可動最大ステップ数
constexpr int STEP_BACK_X = 100;   // X軸のソフトウェア可動範囲マージン
constexpr int STEP_BACK_Y = 200;   // Y軸のソフトウェア可動範囲マージン
constexpr int PHYSICAL_BACK = 300; // スイッチ解除のための物理的な戻り量
constexpr int XSTEP = 3100 * 2 + 500 - STEP_BACK_X * 2;
constexpr int YSTEP = 1500 * 2 + 100 - STEP_BACK_Y;

constexpr long HOMING_CHUNK = -10;

#endif // MOTOR_CONFIG_H_
