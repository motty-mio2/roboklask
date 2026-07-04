#include <AccelStepper.h>
#if defined(ARDUINO_UNO_Q)
#include <Arduino_LED_Matrix.h>
#include <Arduino_RouterBridge.h>
#include <zephyr/kernel.h>
Arduino_LED_Matrix matrix;
K_MUTEX_DEFINE(anim_mtx);
#elif defined(ARDUINO_MINIMA)
#include "receiver.hpp"
SerialBallReceiver receiver(Serial, 115200);
#endif

#include <vector>

#include "pinout.h"
#include "xycontrol.hpp"

XYControl xyControl(MX_STEP, MX_DIR, MY_STEP, MY_DIR);

long targetPos = 1000;

void setup() {
#if defined(ARDUINO_UNO_Q)
  matrix.begin();
  matrix.setGrayscaleBits(1);
  matrix.clear();
  Bridge.begin();
  Monitor.begin();
#elif defined(ARDUINO_MINIMA)
  receiver.begin();
#endif

  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW);  // キャリブレーション完了前は消灯

  pinMode(SW_X, INPUT_PULLUP);
  pinMode(SW_Y, INPUT_PULLUP);

  pinMode(nEN, OUTPUT);
  digitalWrite(nEN, HIGH);

  // 0, 1番ピンのINPUTハック
  if (setM0) {
    pinMode(M0, OUTPUT);
    digitalWrite(M0, true);
  } else {
    pinMode(M0, INPUT);
  }
  if (setM1) {
    pinMode(M1, OUTPUT);
    digitalWrite(M1, true);
  } else {
    pinMode(M1, INPUT);
  }
  pinMode(M2, OUTPUT);
  digitalWrite(M2, setM2);

  // キャリブレーション中はLEDを点灯
  digitalWrite(LED_BUILTIN, HIGH);
  xyControl.homing(SW_X, SW_Y);
  digitalWrite(LED_BUILTIN, LOW);  // 完了したら一旦消灯
  xyControl.gotoCenter();
}

void loop() {
  // 1. モーターのステップを更新（最優先・毎回実行）
  xyControl.run();

#if !defined(ARDUINO_UNO_Q)
  // 2. シリアルポートからボール位置を受信（Minima専用）
  BallPosition pos;
  if (receiver.receive(pos)) {
    // 【通信確認用デバッグ】データを受信するたびにLEDをチカチカ点滅させる
    static bool ledState = false;
    ledState = !ledState;
    digitalWrite(LED_BUILTIN, ledState ? HIGH : LOW);

    // 送信データ範囲 [0.0, 1.0] は XYControl.move の入力範囲 [0.0, 1.0]
    // にそのまま対応
    float x_mapped = pos.x;
    // y: 0.0 (手前) -> 0.0,  1.0 (奥) -> 1.0
    float y_mapped = pos.y;
    // float y_mapped = 0.2f; // テスト用固定値

    xyControl.move(x_mapped, y_mapped);
  }
#endif
}
