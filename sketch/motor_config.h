#ifndef MOTOR_CONFIG_H
#define MOTOR_CONFIG_H_

constexpr int setM0 = true;
constexpr int setM1 = true;
constexpr int setM2 = false;

// モーターのステップ角換算係数
//   旧: ST-42BYH1004-5013 (0.9°/step, 400 steps/rev)  <- 下の定数の基準値
//   新: 17HS4401S         (1.8°/step, 200 steps/rev)
// 同じステップ数では新モーターは 2 倍回るため、全ステップ定数を 1/2 する。
// 旧モーターに戻すときは NUM=1, DEN=1 にすればよい。
constexpr int MOTOR_STEPS_NUM = 1; // 新モーターの steps/rev 比
constexpr int MOTOR_STEPS_DEN = 2; // 旧モーターの steps/rev 比

// 1回転あたりのベースステップ数
constexpr int STEP = 400 * MOTOR_STEPS_NUM / MOTOR_STEPS_DEN;
constexpr int resolution = 8;

// 盤面の可動最大ステップ数
constexpr int STEP_BACK_X =
    100 * MOTOR_STEPS_NUM / MOTOR_STEPS_DEN; // X軸のソフトウェア可動範囲マージン
constexpr int STEP_BACK_Y =
    200 * MOTOR_STEPS_NUM / MOTOR_STEPS_DEN; // Y軸のソフトウェア可動範囲マージン
constexpr int PHYSICAL_BACK =
    300 * MOTOR_STEPS_NUM /
    MOTOR_STEPS_DEN; // スイッチ解除のための物理的な戻り量
constexpr int XSTEP = (3100 * 2 + 500) * MOTOR_STEPS_NUM / MOTOR_STEPS_DEN -
                      STEP_BACK_X * 2;
constexpr int YSTEP =
    (1500 * 2 + 100) * MOTOR_STEPS_NUM / MOTOR_STEPS_DEN - STEP_BACK_Y;

constexpr long HOMING_CHUNK = -10;

// ---------------------------------------------------------------------------
// 速度・加速度（物理単位: rev/s, rev/s^2）
// STEP * resolution で steps/s に変換されるので、モーターを替えても
// MOTOR_STEPS_NUM/DEN に追従する。
//
// 目安: 17HS4401S (200 steps/rev) + 1/8 マイクロステップ = 1600 steps/rev
//   OPERATIONAL_SPEED_RPS = 5.0  -> 300 rpm / 8000 steps/s
//   OPERATIONAL_ACCEL_RPS2 = 8.0 -> 最高速まで 0.625 s
// ストライカーが滑る/脱調する -> ACCEL を下げる
// 動き出しが鈍い            -> ACCEL を上げる（ベルトの張りに注意）
// ---------------------------------------------------------------------------
constexpr float HOMING_SPEED_RPS = 0.5f;
constexpr float HOMING_ACCEL_RPS2 = 1.0f;
constexpr float OPERATIONAL_SPEED_RPS = 5.0f;
constexpr float OPERATIONAL_ACCEL_RPS2 = 8.0f;


#endif // MOTOR_CONFIG_H_
