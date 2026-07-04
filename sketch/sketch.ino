#include <AccelStepper.h>
#if defined(ARDUINO_UNO_Q)
#include <Arduino_LED_Matrix.h>
#include <Arduino_RouterBridge.h>
#include <zephyr/kernel.h>
Arduino_LED_Matrix matrix;
K_MUTEX_DEFINE(anim_mtx);
#elif defined(ARDUINO_MINIMA)
#include "serial_bridge.hpp"
SerialBridge bridge(Serial, 115200);
#endif

#include <vector>

#include "pinout.h"
#include "xycontrol.hpp"

XYControl xyControl(MX_STEP, MX_DIR, MY_STEP, MY_DIR, SW_X, SW_Y);

long targetPos = 1000;

void setup() {
#if defined(ARDUINO_UNO_Q)
  matrix.begin();
  matrix.setGrayscaleBits(1);
  matrix.clear();
  Bridge.begin();
  Monitor.begin();
#elif defined(ARDUINO_MINIMA)
  bridge.begin();
#endif

  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW);  // キャリブレーション完了前は消灯

  pinMode(SW_X, INPUT_PULLUP);
  pinMode(SW_Y, INPUT_PULLUP);

  pinMode(nEN, OUTPUT);
  digitalWrite(nEN, HIGH);

  // M0, M1, M2ピンの出力を明示的に設定
  pinMode(M0, OUTPUT);
  digitalWrite(M0, setM0);
  pinMode(M1, OUTPUT);
  digitalWrite(M1, setM1);
  pinMode(M2, OUTPUT);
  digitalWrite(M2, setM2);

  // キャリブレーション中はLEDを点灯
  digitalWrite(LED_BUILTIN, HIGH);
  xyControl.homing();
  digitalWrite(LED_BUILTIN, LOW);  // 完了したら一旦消灯
  xyControl.gotoCenter();
}

Position new_head_pos;
Position head_pos;

void loop() {
  // 1. モーターのステップを更新（最優先・毎回実行）
  xyControl.run();
  xyControl.getCurrentXY(head_pos);

#if !defined(ARDUINO_UNO_Q)
  // 2. シリアルポートからボール位置を受信し、現在XY位置を返送（Minima専用）
  if (bridge.receive(new_head_pos)) {
    // 【通信確認用デバッグ】データを受信するたびにLEDをチカチカ点滅させる
    static bool ledState = false;
    ledState = !ledState;
    digitalWrite(LED_BUILTIN, ledState ? HIGH : LOW);

    // 送信データ範囲 [0.0, 1.0] は XYControl.move の入力範囲 [0.0, 1.0]
    // にそのまま対応
  }

  // 現在のXY位置をUARTで送信（SerialBridge内で20ms間引き）
  bridge.sendPosition(head_pos);
#endif
  xyControl.move(new_head_pos);
}
