#include <AccelStepper.h>
#include <Arduino.h>

#include "pinout.h"

#if defined(ARDUINO_UNO_Q)
#include <Arduino_LED_Matrix.h>
#include <zephyr/kernel.h>
Arduino_LED_Matrix matrix;
#endif

// Stepper motor driver instances
// AccelStepper::DRIVER = 1 (step pin, direction pin)
AccelStepper stepperX(AccelStepper::DRIVER, MX_STEP, MX_DIR);
AccelStepper stepperY(AccelStepper::DRIVER, MY_STEP, MY_DIR);

// Test motion parameters
constexpr float MAX_SPEED = 800.0f;
constexpr float ACCELERATION = 1200.0f;
constexpr long TEST_STEPS =
    400; // Microstep: 400 steps (about 1/8 to 1 revolution depending on driver)
constexpr unsigned long PAUSE_MS = 600;

void setup() {
  // Built-in LED initialization (LOW = ON, HIGH = OFF for Uno R4)
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, HIGH);

  Serial.begin(115200);
  for (int i = 0; i < 10 && !Serial; i++) {
    delay(100);
  }
  Serial.println("=================================");
  Serial.println("  Roboklask Motor Step Test  ");
  Serial.println("=================================");

#if defined(ARDUINO_UNO_Q)
  matrix.begin();
  matrix.clear();
#endif

  // Enable TMC2209 driver (nEN: active LOW)
  pinMode(nEN, OUTPUT);
  digitalWrite(nEN, LOW);
  Serial.println("[Init] Motor driver enabled (nEN = LOW)");

  // Configure limit switch and sensor pins
  pinMode(SW_X, INPUT_PULLUP);
  pinMode(SW_Y, INPUT_PULLUP);
  pinMode(V_SENSE, INPUT);

  // Configure steppers
  stepperX.setMaxSpeed(MAX_SPEED);
  stepperX.setAcceleration(ACCELERATION);
  stepperY.setMaxSpeed(MAX_SPEED);
  stepperY.setAcceleration(ACCELERATION);

  Serial.println("[Init] Stepper speed and acceleration configured.");
  Serial.println("[Init] Starting loop in 1 second...");
  delay(1000);
}

void runStepperToTarget(AccelStepper &stepper, const char *motorName,
                        const char *dirName, long steps) {
  Serial.print("[Test] ");
  Serial.print(motorName);
  Serial.print(" moving ");
  Serial.print(dirName);
  Serial.print(" (");
  Serial.print(steps);
  Serial.println(" steps)...");

  digitalWrite(LED_BUILTIN, LOW); // LED ON
  stepper.move(steps);
  while (stepper.distanceToGo() != 0) {
    stepper.run();
#if defined(ARDUINO_UNO_Q)
    k_yield();
#endif
  }
  digitalWrite(LED_BUILTIN, HIGH); // LED OFF
  delay(PAUSE_MS);
}

void loop() {
  // Print current pin states
  int sw_x_val = digitalRead(SW_X);
  int sw_y_val = digitalRead(SW_Y);
  int v_sense_val = analogRead(V_SENSE);

  Serial.println("---------------------------------");
  Serial.print("[Status] SW_X: ");
  Serial.print(sw_x_val == LOW ? "TRIGGERED (LOW)" : "OPEN (HIGH)");
  Serial.print(" | SW_Y: ");
  Serial.print(sw_y_val == LOW ? "TRIGGERED (LOW)" : "OPEN (HIGH)");
  Serial.print(" | V_SENSE (A0 raw): ");
  Serial.println(v_sense_val);

  // 1. Motor X (MX) Forward
  runStepperToTarget(stepperX, "Motor X (MX)", "Forward (CW)", TEST_STEPS);

  // 2. Motor X (MX) Backward
  runStepperToTarget(stepperX, "Motor X (MX)", "Backward (CCW)", -TEST_STEPS);

  // 3. Motor Y (MY) Forward
  runStepperToTarget(stepperY, "Motor Y (MY)", "Forward (CW)", TEST_STEPS);

  // 4. Motor Y (MY) Backward
  runStepperToTarget(stepperY, "Motor Y (MY)", "Backward (CCW)", -TEST_STEPS);

  Serial.println("[Cycle Done] Waiting before next cycle...");
  delay(1200);
}
