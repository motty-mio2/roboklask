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

void blinkLED(int count) {
  for (int i = 0; i < count; i++) {
    digitalWrite(LED_BUILTIN, LOW);  // 点灯 (LOW=ON)
    delay(100);
    digitalWrite(LED_BUILTIN, HIGH);  // 消灯 (HIGH=OFF)
    delay(100);
  }
  delay(500);
}

unsigned long long last_update_ms = millis();
constexpr uint8_t CYCLE_ms = 33;

void setup() {
  // 最優先でLEDピンを初期化して消灯(HIGH=OFF)にする
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, HIGH);

  // PC接続用シリアルデバッグの開始
  Serial.begin(115200);
  for (int i = 0; i < 10 && !Serial; i++) {
    delay(100);
  }
  Serial.println("MCU Started.");

  blinkLED(1);  // 1回点滅: setup開始成功 (消灯で終了)

#if defined(ARDUINO_UNO_Q)
  matrix.begin();
  matrix.setGrayscaleBits(1);
  matrix.clear();

  // Bridgeの開始 (Pythonアプリとの通信接続待ちが発生する可能性あり)
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
// Monitor.begin();  // クラッシュ回避のためコメントアウト
#elif defined(ARDUINO_MINIMA)
  bridge.begin();
#endif

  blinkLED(2);  // 2回点滅: Bridge / 通信の初期化成功

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

  blinkLED(3);  // 3回点滅: ピン設定完了、Homing直前

  // キャリブレーション中はLEDを点灯
  digitalWrite(LED_BUILTIN, LOW);  // 点灯 (LOW=ON)
  Serial.println("Starting homing...");
  xyControl.homing();
  digitalWrite(LED_BUILTIN, HIGH);  // 完了したら一旦消灯 (HIGH=OFF)
  Serial.println("Homing finished.");

  blinkLED(4);  // 4回点滅: Homing完了、loop突入直前

  Serial.println("Moving to center (skipped for debug)...");
  // xyControl.gotoCenter();
  Serial.println("Center reached (skipped for debug).");

  blinkLED(5);  // 5回点滅: setup正常終了

  // 初期ターゲットを中央に設定し、loop()突入時の引き戻しを防ぐ
  new_head_pos.x = 0.0f;
  new_head_pos.y = 1.0f;
}

Position local_new_head_pos;
void loop() {
  // xyControl.run();
  now = millis();
  if (now - last_update_ms >= CYCLE_ms) {
    last_update_ms = now;
  }
  // 1. モーターのステップを更新（最優先・毎回実行）
  // xyControl.run();
  // xyControl.getCurrentXY(head_pos);

#if defined(ARDUINO_UNO_Q)
  // 20msごとにPython側へ現在XY位置を通知
  unsigned long now = millis();
  if (now - lastReportMs >= 20) {
    lastReportMs = now;
    Bridge.call("mcu2py", head_pos.x, head_pos.y);
  }
  k_mutex_lock(&xy_mutex, K_FOREVER);
  local_new_head_pos = new_head_pos;
  k_mutex_unlock(&xy_mutex);
  xyControl.move(local_new_head_pos);
#elif defined(ARDUINO_MINIMA)
  // 2. シリアルポートからボール位置を受信し、現在XY位置を返送（Minima専用）
  if (bridge.receive(new_head_pos)) {
    // 【通信確認用デバッグ】データを受信するたびにLEDをチカチカ点滅させる
    static bool ledState = false;
    ledState = !ledState;
  }

  // 現在のXY位置をUARTで送信（SerialBridge内で20ms間引き）
  bridge.sendPosition(head_pos);
  xyControl.move(local_new_head_pos);
#endif
}
