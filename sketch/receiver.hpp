#ifndef RECEIVER_HPP
#define RECEIVER_HPP

#include <Arduino.h>

struct BallPosition {
  float x;
  float y;
};

// Abstract base class for receiving ball coordinates
class BallReceiver {
public:
  virtual bool begin() = 0;
  virtual bool receive(BallPosition &pos) = 0;
};

// Binary Serial implementation for Arduino UNO R4 Minima
class SerialBallReceiver : public BallReceiver {
private:
  HardwareSerial &serialPort;
  unsigned long baudrate;

public:
  SerialBallReceiver(HardwareSerial &port = Serial, unsigned long baud = 115200)
      : serialPort(port), baudrate(baud) {}

  bool begin() override {
    serialPort.begin(baudrate);
    return true;
  }

  bool receive(BallPosition &pos) override {
    // Check if 9 bytes are available in the serial buffer
    // Packet structure: [0xAA] [float x] [float y]
    if (serialPort.available() >= 9) {
      if (serialPort.read() == 0xAA) {
        float x_val, y_val;
        serialPort.readBytes((char*)&x_val, 4);
        serialPort.readBytes((char*)&y_val, 4);

        // If coordinates are nan (lost ball flag), return false
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
};

#endif // RECEIVER_HPP
