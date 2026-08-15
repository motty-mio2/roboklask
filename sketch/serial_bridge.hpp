#ifndef SERIAL_BRIDGE_HPP
#define SERIAL_BRIDGE_HPP
#include <Arduino.h>

#include "xycontrol.hpp"

// Arduino UNO R4 Minima 専用の双方向シリアル通信クラス
// UNO Q は RouterBridge のイベントモデルのため、#ifdef で別管理する
class SerialBridge {
private:
  HardwareSerial &serialPort;
  unsigned long baudrate;
  unsigned long lastSent = 0;

public:
  explicit SerialBridge(HardwareSerial &port = Serial,
                        unsigned long baud = 115200)
      : serialPort(port), baudrate(baud) {}

  bool begin() {
    serialPort.begin(baudrate);
    return true;
  }

  // 受信: ボール位置を受け取る
  // パケット形式: [0xAA][float x 4bytes][float y 4bytes]
  // NaN受信時（ボールロスト）は false を返す
  bool receive(Position &pos) {
    if (serialPort.available() >= 9) {
      if (serialPort.read() == 0xAA) {
        float x_val, y_val;
        serialPort.readBytes(reinterpret_cast<char *>(&x_val), 4);
        serialPort.readBytes(reinterpret_cast<char *>(&y_val), 4);
        if (isnan(x_val) || isnan(y_val)) {
          return false;
        }
        pos.x = x_val;
        pos.y = y_val;
        return true;
      }
    }
    return false;
  }

  // 送信: モーターの現在XY位置を送出する（intervalMs ごとに間引き）
  // パケット形式: [0xAA][float x 4bytes][float y 4bytes]
  void sendPosition(const Position &pos, unsigned long intervalMs = 20) {
    unsigned long current_ms = millis();
    if (current_ms - lastSent < intervalMs)
      return;
    lastSent = current_ms;
    const uint8_t header = 0xAA;
    serialPort.write(&header, 1);
    serialPort.write(reinterpret_cast<const uint8_t *>(&pos.x), 4);
    serialPort.write(reinterpret_cast<const uint8_t *>(&pos.y), 4);
  }
};

#endif // SERIAL_BRIDGE_HPP
