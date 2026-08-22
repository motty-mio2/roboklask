#ifndef MOTOR_CONFIG_H
#define MOTOR_CONFIG_H_

constexpr int setM0 = false;
constexpr int setM1 = true;
constexpr int setM2 = false;

// 1回転あたりのベースステップ数
constexpr int STEP = 400;
constexpr int resolution = 4;

// 盤面の可動最大ステップ数
constexpr int STEP_BACK = 100;     // ソフトウェアの可動範囲マージン
constexpr int PHYSICAL_BACK = 300; // 物理的なリミットスイッチ離脱距離
constexpr int XSTEP = 3100 * 2 - STEP_BACK * 2;
constexpr int YSTEP = 1500 * 2 - STEP_BACK;

constexpr long HOMING_CHUNK = -10;

#endif // MOTOR_CONFIG_H_
