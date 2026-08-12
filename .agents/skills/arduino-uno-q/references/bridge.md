# SKILL: Arduino UNO Q Bridge API

## 概要
Arduino UNO QのBridge APIは、Linuxマイクロプロセッサ（MPU）上のPythonロジックと、Arduinoマイクロコントローラ（MCU）上のリアルタイムなC++スケッチ間で双方向通信（RPC）を行うためのレイヤーです [1]。裏側では`arduino-router`サービスがMessagePack RPCプロトコルを用いてネットワークを管理しており、通信時の最大メッセージサイズは256バイトに制限されています [2]。

## API仕様詳細と制約

### 1. C++ API (MCU / Arduinoスケッチ側)
実装には `<Bridge.h>` をインクルードして使用します [3]。
*   **初期化**: `setup()` 関数内で他のBridgeメソッドを使用する前に `Bridge.begin()` を呼び出し、内部のシリアルトランスポートを初期化します [3]。
*   **送信 (Python関数の呼び出し)**:
    *   `Bridge.call("メソッド名", 引数...)`: Linux側の登録された関数を呼び出し、結果が返るまで実行をブロック（待機）します [3]。
    *   `Bridge.notify("メソッド名", 引数...)`: 応答を待たずに非同期でデータを送信（Fire-and-forget）します [4]。256バイトを超えたメッセージは破棄されます [4]。
*   **受信 (関数の公開)**:
    *   `Bridge.provide("名前", コールバック)`: 高優先度のバックグラウンドRPCスレッドで実行される関数を登録します [4]。処理は短くスレッドセーフである必要があります [4]。**警告**: デッドロックを防ぐため、このコールバック内部で `Bridge.call()` や `Monitor.print()` を使用してはいけません [5]。
    *   `Bridge.register("名前", コールバック)`: メインの `loop()` コンテキスト内で実行される関数を登録します [5]。`delay()` や `Wire` などの標準Arduino APIと連携する場合は、クラッシュを防ぐためにこちらを使用してください [5, 6]。

### 2. Python API (MPU / Linux側)
`bridge` モジュールから `Bridge` クラスをインポートして使用します [6]。
*   **送信 (MCU関数の呼び出し)**:
    *   `Bridge.call("メソッド名", 引数...)`: MCU側の関数を呼び出し、結果をブロックして待機します [6]。256バイト制限を超えると例外が発生します [6]。
    *   `Bridge.notify("メソッド名", 引数...)`: MCUの関数へ、応答を待たずに非同期で送信します [7]。
*   **受信 (関数の公開)**:
    *   `Bridge.register("タグ", コールバック)`: MCUからの要求に一致するタグを受け取った際に呼び出されるPython関数を登録します [7]。

### 3. データ型のマッピング (MsgPack)
Bridgeライブラリは、PythonとC++間のデータ型をMsgPackを使用して自動的にシリアライズ・デシリアライズします [8]。
*   Python `list` ⇔ C++ `std::vector`, `std::array`, `std::list` [8]
*   Python `dict` ⇔ C++ `std::map` [8]
*   Python `str` ⇔ C++ `char*`, `String` [8]
*   Python `bytes` ⇔ C++ `std::vector<uint8_t>`, `arduino::msgpack::arr_t<uint8_t>` [8]
*   Python `None` ⇔ C++ `void` [8]

### 4. Monitor API
従来のUSB CDCシリアルポート（`Serial.print`など）の代わりに、仮想シリアルモニターとして機能する Monitor API を使用します [8]。
*   `Monitor.begin()` で初期化します [9]。
*   `Monitor.print(データ)` や `Monitor.println(データ)` でシリアルモニターへデータを送信します [9]。
*   `Monitor.read()` で受信データを読み取りますが、現在のC++実装ではキューが空の場合、標準のStreamクラスと異なり **`-1` ではなく `0` を返す**仕様に注意してください [9]。

## References
*   [Bridge API Reference | Arduino Documentation](https://docs.arduino.cc/software/app-lab/bridge/bridge-api/)
*   [Working with Arduino Router RPC | Arduino Documentation](https://docs.arduino.cc/tutorials/uno-q/rou