#include <AccelStepper.h>
#if defined(ARDUINO_UNO_Q)
#include <Arduino_RouterBridge.h>
#include <zephyr/kernel.h>

#include "matrix.h"
Arduino_LED_Matrix matrix;
K_MUTEX_DEFINE(head_mutex);
K_MUTEX_DEFINE(ball_mutex);
#elif defined(ARDUINO_MINIMA)
#include "serial_bridge.hpp"
SerialBridge bridge(Serial, 115200);
#endif

#include <vector>

#include "pinout.h"
#include "xycontrol.hpp"

XYControl xyControl(MX_STEP, MX_DIR, MY_STEP, MY_DIR, SW_X, SW_Y);

Position new_head_pos;
Position head_pos;
Position ball_pos; // 追加: loopでの描画用

void blinkLED(int count) {
  for (int i = 0; i < count; i++) {
    digitalWrite(LED_BUILTIN, LOW); // 点灯 (LOW=ON)
    delay(100);
    digitalWrite(LED_BUILTIN, HIGH); // 消灯 (HIGH=OFF)
    delay(100);
  }
  delay(500);
}

unsigned long now = 0;
unsigned long last_update_ms = 0;
constexpr uint8_t CYCLE_ms = 33;

void setup() {
  // 1. 最優先でLEDピンを初期化して消灯(HIGH=OFF)にする
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, HIGH);

  // PC接続用シリアルデバッグの開始
  Serial.begin(115200);
  for (int i = 0; i < 10 && !Serial; i++) {
    delay(100);
  }
  Serial.println("MCU Started.");

  blinkLED(1); // 1回点滅: setup開始成功 (消灯で終了)

#if defined(ARDUINO_UNO_Q)
  // LED Matrixの初期化のみ最初に行う
  matrix.begin();
  matrix.setGrayscaleBits(1);
  matrix.clear();
#endif

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

  blinkLED(2); // 2回点滅: ピン初期設定完了、Homing直前

  // 2. キャリブレーションの実行
  // (この時点ではBridge通信は始まっていないため完全に安全)
  digitalWrite(LED_BUILTIN, LOW); // 点灯 (LOW=ON)
  Serial.println("Starting homing...");
  xyControl.homing();
  digitalWrite(LED_BUILTIN, HIGH); // 完了したら一旦消灯 (HIGH=OFF)
  Serial.println("Homing finished.");

  // 四隅巡回テストの実行
  Serial.println("Starting test corners...");
  xyControl.testCorners();
  Serial.println("Test corners finished.");

  blinkLED(3); // 3回点滅: Homing完了、gotoCenter直前

  Serial.println("Moving to center...");
  xyControl.gotoCenter(); // 中央へ移動
  Serial.println("Center reached.");

  blinkLED(4); // 4回点滅: Center移動完了、通信初期化直前

  // 3. モーターのすべての初期位置合わせが完了した後に、通信を開始する
#if defined(ARDUINO_UNO_Q)
  Bridge.begin();

  Bridge.provide("py2mcu", [](float tx, float ty, float bx, float by) {
    k_mutex_lock(&head_mutex, K_FOREVER);
    new_head_pos.x = constrain(tx, -1.0f, 1.0f);
    new_head_pos.y = constrain(ty, 0.0f, 1.0f);
    k_mutex_unlock(&head_mutex);

    k_mutex_lock(&ball_mutex, K_FOREVER);
    ball_pos.x = bx;
    ball_pos.y = by;
    k_mutex_unlock(&ball_mutex);

    // データ受信のたびにLEDをトグルして、受信割り込みの動作を目視確認する
    static bool ledState = false;
    ledState = !ledState;
    digitalWrite(LED_BUILTIN, ledState ? LOW : HIGH); // LOW=ON, HIGH=OFF
  });

  Monitor.begin(); // クラッシュ回避のためコメントアウト
#elif defined(ARDUINO_MINIMA)
  bridge.begin();
#endif

  blinkLED(5); // 5回点滅: 通信初期化完了、setup正常終了

  // 初期ターゲットを中央に設定し、loop()突入時の引き戻しを防ぐ
  new_head_pos.x = 0.0f;
  new_head_pos.y = 1.0f;
  ball_pos.x = 0.0f;
  ball_pos.y = 0.0f;
}

Position local_new_head_pos;
Position local_ball_pos;

void loop() {
  // 1. モーターのステップを更新（最優先・毎ループ実行）
  // 33msの制御・通信周期によるディレイに影響されず、ステップパルスを生成し続けるため最優先で呼び出します
  xyControl.run();

  now = millis();
  if (now - last_update_ms < CYCLE_ms) {
#if defined(ARDUINO_UNO_Q)
    safeUpdate(); // Bridgeの受信処理を直接実行してキューイングを防止する
#endif
    return;
  }
  last_update_ms = now;

  xyControl.getCurrentXY(head_pos);

#if defined(ARDUINO_UNO_Q)
  Bridge.notify("mcu2py", head_pos.x, head_pos.y);

  // 割り込みスレッドで更新されたターゲット座標を安全にコピーして、モーター制御に反映する
  k_mutex_lock(&head_mutex, K_FOREVER);
  local_new_head_pos = new_head_pos;
  k_mutex_unlock(&head_mutex);
  xyControl.move(local_new_head_pos);

  // LED Matrixの描画は、安全なメインスレッド(loop)側で実行する
  k_mutex_lock(&ball_mutex, K_FOREVER);
  local_ball_pos = ball_pos;
  k_mutex_unlock(&ball_mutex);
  xy(matrix, local_ball_pos.x, local_ball_pos.y);

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
