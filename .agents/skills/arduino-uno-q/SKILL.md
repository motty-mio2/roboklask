---
name: arduino-uno-q
description: Arduino UNO Q (UNO R4 / Minima) ボード開発、MPU-MCU間の通信、App Lab、App Bricks、および Bridge API についての知識と手順を提供します。
---

# SKILL.md: Arduino UNO Q

## 概要
このスキルは、Arduino UNO Q ボードにおける開発基盤、特に Linux マイクロプロセッサ (MPU) と Arduino マイクロコントローラ (MCU) 間を連携させる Bridge API、およびボード固有の実装手順を提供します。

---

## 1. 接続方式の選択 (UNO Q vs Minima)
本プロジェクトでは、対象となるターゲットボードに応じて通信および運動制御ポリシーのレイヤーが異なります。

* **UNO R4 (UNO Q / Zephyr RTOS)**:
  * **通信方式**: `Bridge` 通信 (MessagePack RPC)
  * **設定**: `KLASK_OUTPUT_TYPE=bridge`
  * **特徴**: Zephyr RTOS カーネル上で動作し、LEDマトリクス表示、および Bridge API による非同期・同期RPCを利用します。
* **Minima (Arduino UNO R4 Minima)**:
  * **通信方式**: UART シリアル通信 (115200 baud)
  * **設定**: `KLASK_OUTPUT_TYPE=uart`
  * **特徴**: リアルタイム処理ループで UART の特定ヘッダー (`0xAA`) に基づくバイナリパケットを直接処理します。

---

## 2. MCU 側 (C++ スケッチ) の Bridge 実装手順

UNO Q で Bridge 通信を行う場合、以下の手順とテンプレートに従って実装します。

### 実装テンプレート
```cpp
#include <Arduino_RouterBridge.h>
#include <zephyr/kernel.h> // Zephyr カーネルのヘッダー

// 共有データアクセス用のミューテックスを定義
K_MUTEX_DEFINE(xy_mutex);

struct Position {
  float x;
  float y;
} new_head_pos, head_pos;

unsigned long lastReportMs = 0;

void setup() {
  // Bridge APIの初期化
  Bridge.begin();

  // Python(MPU)側から呼び出されるRPC/通知のコールバック登録
  Bridge.provide("xy", [](float x, float y) {
    // コールバックは別スレッドで実行されるため、必ずロックを取得する
    k_mutex_lock(&xy_mutex, K_FOREVER);
    new_head_pos.x = x;
    new_head_pos.y = y;
    k_mutex_unlock(&xy_mutex);
  });

  Monitor.begin();
}

void loop() {
  // 共有変数を安全にローカルにコピーして利用する
  Position local_target;
  k_mutex_lock(&xy_mutex, K_FOREVER);
  local_target = new_head_pos;
  k_mutex_unlock(&xy_mutex);

  // 運動制御への適用など
  // xyControl.move(local_target);

  // Python(MPU)側への周期的な座標通知 (非ブロッキングで20ms周期を維持)
  unsigned long now = millis();
  if (now - lastReportMs >= 20) {
    lastReportMs = now;
    // MPU側の report_xy プロバイダを呼び出す
    Bridge.call("report_xy", head_pos.x, head_pos.y);
  }
}
```

### 【重要】マルチスレッドとスレッドセーフティ
* **RPC コールバックのスレッド**: `Bridge.provide` で登録されたコールバックは、メインの `loop()` とは異なるスレッド（Bridge サービススレッド）で実行されます。
* **排他制御**: `loop()` 内とコールバック内で共有されるすべての変数（例: ターゲット座標など）は、Zephyr カーネルのプリミティブである `K_MUTEX_DEFINE` マクロで定義した `k_mutex` を用いて、`k_mutex_lock` および `k_mutex_unlock` で保護してください。

---

## 3. MPU 側 (Python) の Bridge 実装手順

Python アプリケーション側では、`arduino-app-bricks` に含まれる Bridge API を使用して接続モジュールを実装します。

### 実装テンプレート (`bridge_connection.py` 相当)
```python
import threading
from arduino.app_utils import Bridge
from python.domain import RobotXY
from python.domain.mcu_connection import McuConnection

class BridgeMcuConnection(McuConnection):
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._latest_feedback: RobotXY | None = None

    def start(self) -> None:
        try:
            # MCUからの report_xy 呼び出しを処理するコールバックを登録
            Bridge.provide("report_xy", self._on_feedback)
        except Exception as e:
            print(f"Error starting bridge: {e}")

    def _on_feedback(self, x: float, y: float) -> None:
        # コールバックはサブスレッドから呼び出されるため threading.Lock で保護
        feedback = RobotXY(x=x, y=y)
        with self._lock:
            self._latest_feedback = feedback

    def send_target(self, target: RobotXY | None) -> None:
        if target is None:
            return
        try:
            # メインの画像処理・推論ループをブロックしないために notify (非同期RPC) を使用
            Bridge.notify("xy", target.x, target.y)
        except Exception as e:
            print(f"Error sending coordinates: {e}")

    def read_feedback(self) -> RobotXY | None:
        with self._lock:
            feedback = self._latest_feedback
            self._latest_feedback = None  # 読み取り後はリセット
        return feedback

    def stop(self) -> None:
        try:
            # コールバックの登録解除
            Bridge.unprovide("report_xy")
        except Exception as e:
            print(f"Error stopping bridge: {e}")
```

### 実装時の注意点
1. **ブロッキングの回避**: 座標送信には `Bridge.call` ではなく `Bridge.notify` を使用してください。`call` は応答を待機するため、20ms などの高速な画像処理ループ（メインスレッド）を停止させ、ジッターを発生させる原因になります。
2. **メッセージバッファ制限**: `arduino-router` 経由の RPC 送信メッセージサイズは最大 **256バイト** です。大量のデータや複雑な構造体を一度に送信しないでください。

---

## 4. リファレンスとドキュメント
* [Working with Arduino Router RPC | Arduino Documentation](https://docs.arduino.cc/tutorials/uno-q/routerbridge-multilanguage/)
* [Bridge API Reference | Arduino Documentation](https://docs.arduino.cc/software/app-lab/bridge/bridge-api/)
* [GitHub - arduino/app-bricks-examples](https://github.com/arduino/app-bricks-examples)