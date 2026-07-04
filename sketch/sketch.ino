#include <AccelStepper.h>
#if defined(ARDUINO_UNO_Q)
#include <Arduino_LED_Matrix.h>
#include <Arduino_RouterBridge.h>
#include <zephyr/kernel.h>
Arduino_LED_Matrix matrix;
K_MUTEX_DEFINE(anim_mtx);
#endif

#include <vector>

#include "pinout.h"
#include "xycontrol.hpp"

XYControl xyControl(MX_STEP, MX_DIR, MY_STEP, MY_DIR);

// Bridge providers run on a separate thread from loop().
// This mutex protects shared animation state and serializes LED matrix writes.
long targetPos = 1000;

void setup() {
#if defined(ARDUINO_UNO_Q)

  matrix.begin();
  matrix.setGrayscaleBits(1);
  matrix.clear();

  Bridge.begin();

  Monitor.begin();
#endif

  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, HIGH); // キャリブレーション中点灯

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

  xyControl.homing(SW_X, SW_Y);
}

void loop() {
  // // 1. モーターを動かす（最優先で呼ぶ）
  // stepper1.run();

  // // 2. 目標地点に着いたら反転する
  // if (stepper1.distanceToGo() == 0) {
  //   Serial.print("Reached target! Current: ");
  //   Serial.println(stepper1.currentPosition());

  //   delay(500);              // 少し止まってから反対へ
  //   targetPos = -targetPos;  // 4000 ↔ -4000
  //   stepper1.moveTo(targetPos);

  //   Serial.print("Next target set to: ");
  //   Serial.println(targetPos);
  // }

  // // 3. 定期的に現在地をprintする（100msごとなど、やりすぎ注意）
  // static unsigned long lastPrint = 0;
  // if (millis() - lastPrint > 100) {
  //   // 動作が重くならないよう、動いている最中も軽く表示
  //   Monitor.print("Pos: ");
  //   Monitor.println(stepper1.currentPosition());
  //   lastPrint = millis();
  // }
}
