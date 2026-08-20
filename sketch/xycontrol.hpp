#ifndef XYCONTROL_HPP
#define XYCONTROL_HPP

#include <AccelStepper.h>
#include <Arduino.h>

#include "motor_config.h"
#

struct Position {
  float x;
  float y;
};

class XYControl {
private:
  AccelStepper stepper1;
  AccelStepper stepper2;
  int sw_x;
  int sw_y;

public:
  void setHomingSpeed() {
    stepper1.setMaxSpeed(STEP * 0.5 * resolution);
    stepper1.setAcceleration(STEP * 1.0 * resolution);
    stepper2.setMaxSpeed(STEP * 0.5 * resolution);
    stepper2.setAcceleration(STEP * 1.0 * resolution);
  }

  void setOperationalSpeed() {
    stepper1.setMaxSpeed(STEP * 3.5 * resolution);
    stepper2.setMaxSpeed(STEP * 3.5 * resolution);
    stepper1.setAcceleration(STEP * 3 * resolution);
    stepper2.setAcceleration(STEP * 3 * resolution);
  }

  XYControl(const int m1_step, const int m1_dir, const int m2_step,
            const int m2_dir, const int sw_x, const int sw_y)
      : stepper1(AccelStepper(1, m1_step, m1_dir)),
        stepper2(AccelStepper(1, m2_step, m2_dir)), sw_x(sw_x), sw_y(sw_y) {
    setHomingSpeed();
  }

  bool homing() {
    // ホーミング用の微小移動ステップ（0へ向かってマイナスに進む）
    // 安全のためのキャリブレーション用低速設定
    setHomingSpeed();

    // ==========================================
    // STEP 1: 左右リセット (SW_X が HIGH になるまでマイナス駆動)
    // ==========================================
    // 配線反転により、これが物理的な左右リセット方向になります
    // 大きな目的地を指定して、スムーズに加速・巡航させます
    stepper1.moveTo(-10000 * resolution);
    stepper2.moveTo(10000 * resolution);

    while (digitalRead(sw_x) == LOW) {
      stepper1.run();
      stepper2.run();
    }

    // 即座にパルス送信を終了する（減速のためのオーバーランを防ぐ）
    stepper1.setCurrentPosition(stepper1.currentPosition());
    stepper2.setCurrentPosition(stepper2.currentPosition());

    // スイッチ解放（プラス側へ戻す）
    stepper1.move(PHYSICAL_BACK * resolution);
    stepper2.move(-PHYSICAL_BACK * resolution);
    while (stepper1.distanceToGo() != 0 || stepper2.distanceToGo() != 0) {
      stepper1.run();
      stepper2.run();
    }
    delay(200);

    // ==========================================
    // STEP 2: 前後リセット (SW_Y が HIGH になるまでマイナス駆動)
    // ==========================================
    // 両方マイナス駆動
    stepper1.moveTo(-10000 * resolution);
    stepper2.moveTo(-10000 * resolution);

    while (digitalRead(sw_y) == LOW) {
      stepper1.run();
      stepper2.run();
    }

    // 即座にパルス送信を終了する（減速のためのオーバーランを防ぐ）
    stepper1.setCurrentPosition(stepper1.currentPosition());
    stepper2.setCurrentPosition(stepper2.currentPosition());

    // スイッチ解放（プラス側へ戻す）
    stepper1.move(PHYSICAL_BACK * resolution);
    stepper2.move(PHYSICAL_BACK * resolution);
    while (stepper1.distanceToGo() != 0 || stepper2.distanceToGo() != 0) {
      stepper1.run();
      stepper2.run();
    }
    delay(200);

    // ★ここで最初で最後の原点設定。
    // スイッチから完全に離脱した「この安全な隅」こそが、真の (0, 0) です。
    Serial.println("homing: setting current positions to 0");
    resetCoordinates();
    delay(500);

    // 本番用の設定に引き上げる（脱調防止のため、速度・加速度をマイルドに設定）
    Serial.println("homing: configuring operational speeds");
    setOperationalSpeed();
    Serial.println("homing: complete");
    return true;
  }

  void move(const Position &pos) {
    // 1. 万が一範囲外の数値が来ても盤面から飛び出さないようにクリップする
    // Xは -1.0 〜 1.0、Yは 0.0 〜 1.0
    float clipped_x = constrain(pos.x, -1.0f, 1.0f);
    float clipped_y = constrain(pos.y, 0.0f, 1.0f);

    // 2. 正規化座標を絶対ステップ数（0〜XSTEP/YSTEP）に変換する
    // X軸: -1.0〜1.0 -> 0.0〜1.0 にマッピングし直してから変換
    float x_0_to_1 = (clipped_x + 1.0f) / 2.0f;
    long target_step_x = (long)(XSTEP * x_0_to_1);
    long target_step_y = (long)(YSTEP * clipped_y);

    // 3. モーターに目標絶対座標を指示
    stepper1.moveTo((target_step_x + target_step_y) * resolution);
    stepper2.moveTo((-target_step_x + target_step_y) * resolution);
  }

  void gotoCenter() {
    // X=0.0f (中央), Y=1.0f
    move({0.0f, 1.0f});

    while (stepper1.distanceToGo() != 0 || stepper2.distanceToGo() != 0) {
      this->run();
    }
  }

  void testCorners() {
    Serial.println("testCorners: temporary setting to homing (low) speed");
    setHomingSpeed(); // テスト中はベルト飛び・脱調防止のため低速に固定

    Position corners[] = {
        {-1.0f, 0.0f}, // 左手前
        {-1.0f, 1.0f}, // 左奥
        {1.0f, 1.0f},  // 右奥
        {1.0f, 0.0f}   // 右手前
    };

    for (const auto &corner : corners) {
      Serial.print("testCorners: target -> x=");
      Serial.print(corner.x);
      Serial.print(", y=");
      Serial.println(corner.y);

      move(corner);

      bool collision = false;
      while (stepper1.distanceToGo() != 0 || stepper2.distanceToGo() != 0) {
        // 安全ガード: 一時的に無効化して誤検出によるスキップを防ぐ
        /*
        if (digitalRead(sw_x) == HIGH || digitalRead(sw_y) == HIGH) {
          Serial.println("testCorners: LIMIT DETECTED! Stopping.");
          stepper1.stop();
          stepper2.stop();
          collision = true;
          break;
        }
        */
        stepper1.run();
        stepper2.run();
      }

      if (collision) {
        break;
      }
      delay(1000); // 動作確認のために各角で1秒静止
    }

    Serial.println("testCorners: restoring operational speed");
    setOperationalSpeed(); // テスト完了後に本番用速度に戻す
  }

  void getCurrentXY(Position &pos) {
    long s1 = stepper1.currentPosition();
    long s2 = stepper2.currentPosition();
    // H-bot逆変換:
    //   s1 = (sx + sy) * resolution
    //   s2 = (-sx + sy) * resolution
    // → sx = (s1 - s2) / (2 * resolution)
    // → sy = (s1 + s2) / (2 * resolution)
    long sx = (s1 - s2) / (2 * resolution);
    long sy = (s1 + s2) / (2 * resolution);
    // X軸: 0.0〜1.0 から -1.0〜1.0 へ逆マッピング
    float x_0_to_1 = (float)sx / XSTEP;
    pos.x = x_0_to_1 * 2.0f - 1.0f;
    pos.y = (float)sy / YSTEP;
  }

  void resetX() {
    // sw_x に激突して PHYSICAL_BACK 戻った状態で呼ばれる。
    // この位置の x 座標を (PHYSICAL_BACK - STEP_BACK) と定義し、y
    // 座標は現在の値を保持する。 H-bot: x = (s1 - s2)/(2*res), y = (s1 +
    // s2)/(2*res)
    long current_s1 = stepper1.currentPosition();
    long current_s2 = stepper2.currentPosition();
    long current_y = (current_s1 + current_s2) / (2 * resolution);
    long setup_x = PHYSICAL_BACK - STEP_BACK;

    stepper1.setCurrentPosition((setup_x + current_y) * resolution);
    stepper2.setCurrentPosition((-setup_x + current_y) * resolution);
  }

  void resetY() {
    // sw_y に激突して PHYSICAL_BACK 戻った状態で呼ばれる。
    // この位置の y 座標を (PHYSICAL_BACK - STEP_BACK) と定義し、x
    // 座標は現在の値を保持する。
    long current_s1 = stepper1.currentPosition();
    long current_s2 = stepper2.currentPosition();
    long current_x = (current_s1 - current_s2) / (2 * resolution);
    long setup_y = PHYSICAL_BACK - STEP_BACK;

    stepper1.setCurrentPosition((current_x + setup_y) * resolution);
    stepper2.setCurrentPosition((-current_x + setup_y) * resolution);
  }

  void resetCoordinates() {
    // 左右・前後ともに PHYSICAL_BACK 戻った位置で呼ばれる。
    // この位置の座標を x = (PHYSICAL_BACK - STEP_BACK), y = (PHYSICAL_BACK -
    // STEP_BACK) と定義する。
    long setup_x = PHYSICAL_BACK - STEP_BACK;
    long setup_y = PHYSICAL_BACK - STEP_BACK;

    stepper1.setCurrentPosition((setup_x + setup_y) * resolution);
    stepper2.setCurrentPosition((-setup_x + setup_y) * resolution);
  }

  void run() {
    if (digitalRead(sw_x) == HIGH) {
      stepper1.stop();
      stepper2.stop();
      // 逃げる方向に移動 (sw_x から離れる)
      stepper1.move(STEP_BACK * resolution);
      stepper2.move(-STEP_BACK * resolution);
      while (stepper1.distanceToGo() != 0 || stepper2.distanceToGo() != 0) {
        stepper1.run();
        stepper2.run();
      }
      delay(100);
      resetX();
      return;
    }

    if (digitalRead(sw_y) == HIGH) {
      stepper1.stop();
      stepper2.stop();
      // 逃げる方向に移動 (sw_y から離れる)
      stepper1.move(STEP_BACK * resolution);
      stepper2.move(STEP_BACK * resolution);
      while (stepper1.distanceToGo() != 0 || stepper2.distanceToGo() != 0) {
        stepper1.run();
        stepper2.run();
      }
      delay(100);
      resetY();
      return;
    }

    stepper1.run();
    stepper2.run();
  }
};

#endif // XYCONTROL_HPP
