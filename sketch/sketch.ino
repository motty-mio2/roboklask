#include <AccelStepper.h>
#if defined(ARDUINO_UNO_Q)
#include <Arduino_RouterBridge.h>
#include <zephyr/kernel.h>

#include "matrix.h"
Arduino_LED_Matrix matrix;
K_MUTEX_DEFINE(xy_mutex);
unsigned long lastReportMs = 0;
#elif defined(ARDUINO_MINIMA)
#include "serial_bridge.hpp"
SerialBridge bridge(Serial, 115200);
#endif

#include <vector>

#include "pinout.h"
#include "xycontrol.hpp"

XYControl xyControl(MX_STEP, MX_DIR, MY_STEP, MY_DIR, SW_X, SW_Y);

long targetPos = 1000;

Position new_head_pos;
Position head_pos;

void setup() {
#if defined(ARDUINO_UNO_Q)
  matrix.begin();
  matrix.setGrayscaleBits(1);
  matrix.clear();
  Bridge.begin();
  Bridge.provide("py2mcu", [](float x, float y) {
    k_mutex_lock(&xy_mutex, K_FOREVER);
    new_head_pos.x = constrain(x, 0.0f, 1.0f);
    new_head_pos.y = constrain(y, -1.0f, 1.0f);
    k_mutex_unlock(&xy_mutex);
  });
  Bridge.provide("ball", [](float x, float y) {
    // 受信したボール位置をそのまま表示する
    xy(matrix, x, y);
  });
  Monitor.begin(115200);
#elif defined(ARDUINO_MINIMA)
  bridge.begin();
#endif

  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, HIGH);  // キャリブレーション完了前は消灯 (HIGH=OFF)

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
  Monitor.println("Homing ...");
  digitalWrite(LED_BUILTIN, LOW);  // 点灯 (LOW=ON)
  xyControl.homing();
  Monitor.println("Homing OK");

  digitalWrite(LED_BUILTIN, HIGH);  // 完了したら一旦消灯 (HIGH=OFF)
  Monitor.print("Go to center ...");
  xyControl.gotoCenter();

  // 初期ターゲットを中央に設定し、loop()突入時の引き戻しを防ぐ
  new_head_pos.x = 0.0f;
  new_head_pos.y = 1.0f;
}

void loop() {
  // 1. モーターのステップを更新（最優先・毎回実行）
  xyControl.run();
  xyControl.getCurrentXY(head_pos);

#if defined(ARDUINO_UNO_Q)
  // 20msごとにPython側へ現在XY位置を通知
  unsigned long now = millis();
  if (now - lastReportMs >= 20) {
    lastReportMs = now;
    Bridge.call("mcu2py", head_pos.x, head_pos.y);
  }
#elif defined(ARDUINO_MINIMA)
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

  Position local_new_head_pos;
#if defined(ARDUINO_UNO_Q)
  k_mutex_lock(&xy_mutex, K_FOREVER);
  local_new_head_pos = new_head_pos;
  k_mutex_unlock(&xy_mutex);
#elif defined(ARDUINO_MINIMA)
  local_new_head_pos = new_head_pos;
#endif

  xyControl.move(local_new_head_pos);
}
