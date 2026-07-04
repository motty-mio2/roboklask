#ifndef XYCONTROL_HPP
#define XYCONTROL_HPP

#include <AccelStepper.h>
#include <Arduino.h>

#include "motor_config.h"

class XYControl {
 private:
  AccelStepper stepper1;
  AccelStepper stepper2;

 public:
  XYControl(const int m1_step, const int m1_dir, const int m2_step,
            const int m2_dir)
      : stepper1(AccelStepper(1, m1_step, m1_dir)),
        stepper2(AccelStepper(1, m2_step, m2_dir)) {
    stepper1.setMaxSpeed(STEP * 3 * resolution);
    stepper1.setAcceleration(STEP * 3 * resolution);
    stepper2.setMaxSpeed(STEP * 3 * resolution);
    stepper2.setAcceleration(STEP * 3 * resolution);
  }

  bool homing(const int sw_x, const int sw_y) {
    // ホーミング用の微小移動ステップ（0へ向かってマイナスに進む）
    // 安全のためのキャリブレーション用低速設定
    stepper1.setMaxSpeed(STEP * 3 * resolution);
    stepper1.setAcceleration(STEP * 3 * resolution);
    stepper2.setMaxSpeed(STEP * 3 * resolution);
    stepper2.setAcceleration(STEP * 3 * resolution);

    // ==========================================
    // STEP 1: 左右リセット (SW_X が HIGH になるまでマイナス駆動)
    // ==========================================
    while (digitalRead(sw_x) == LOW) {
      if (stepper1.distanceToGo() == 0 && stepper2.distanceToGo() == 0) {
        // 配線反転により、これが物理的な左右リセット方向になります
        stepper1.move(+HOMING_CHUNK);  // (-)
        stepper2.move(-HOMING_CHUNK);  // (+)
      }
      stepper1.run();
      stepper2.run();
    }

    stepper1.stop();
    stepper2.stop();

    stepper1.move(STEP_BACK);
    stepper2.move(-STEP_BACK);
    while (stepper1.distanceToGo() != 0 || stepper2.distanceToGo() != 0) {
      stepper1.run();
      stepper2.run();
    }
    delay(200);

    // ==========================================
    // STEP 2: 前後リセット (SW_Y が HIGH になるまでマイナス駆動)
    // ==========================================
    while (digitalRead(sw_y) == LOW) {
      if (stepper1.distanceToGo() == 0 && stepper2.distanceToGo() == 0) {
        // 配線反転により、これが物理的な前後リセット方向になります
        stepper1.move(HOMING_CHUNK);  // (-)
        stepper2.move(HOMING_CHUNK);  // (-)
      }
      stepper1.run();
      stepper2.run();
    }

    stepper1.stop();
    stepper2.stop();

    // スイッチ解放（プラス側へ100戻す）
    stepper1.move(STEP_BACK);
    stepper2.move(STEP_BACK);
    while (stepper1.distanceToGo() != 0 || stepper2.distanceToGo() != 0) {
      stepper1.run();
      stepper2.run();
    }
    delay(200);

    // ★ここで最初で最後の原点設定。
    // スイッチから完全に離脱した「この安全な隅」こそが、真の (0, 0) です。
    stepper1.setCurrentPosition(0);
    stepper2.setCurrentPosition(0);
    delay(500);

    // 本番用の設定に引き上げる（脱調防止のため、速度・加速度をマイルドに設定）
    stepper1.setMaxSpeed(STEP * 5 * resolution);
    stepper2.setMaxSpeed(STEP * 5 * resolution);
    stepper1.setAcceleration(STEP * 5 * resolution);
    stepper2.setAcceleration(STEP * 5 * resolution);
  }

  void move(const float x, const float y) {
    // 1. 万が一範囲外の数値が来ても盤面から飛び出さないように 0.0 〜 1.0
    // にクリップする
    float clipped_x = constrain(x, 0.0f, 1.0f);
    float clipped_y = constrain(y, 0.0f, 1.0f);

    // 2. 正規化座標（0〜1）を絶対ステップ数（0〜XSTEP/YSTEP）に変換する
    // AccelStepperは long 型の絶対座標を受け取るため、四捨五入してキャスト
    long target_step_x = (long)(XSTEP * clipped_x);
    long target_step_y = (long)(YSTEP * clipped_y);

    // 3. モーターに目標絶対座標を指示
    // stepper1.moveTo(target_step_x);
    // stepper2.moveTo(target_step_y);
    stepper1.moveTo((target_step_x + target_step_y) * resolution);
    stepper2.moveTo((-target_step_x + target_step_y) * resolution);
  }

  void gotoCenter() {
    move(0.5f, 1.0f);

    while (stepper1.distanceToGo() != 0 || stepper2.distanceToGo() != 0) {
      this->run();
    }
  }

  void run() {
    if (digitalRead(SW_X) == HIGH || digitalRead(SW_Y) == HIGH) {
      stepper1.stop();
      stepper2.stop();
    }
    stepper1.run();
    stepper2.run();
  }
};

#endif  // XYCONTROL_HPP
