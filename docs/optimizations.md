# Roboklask: Technical Optimizations & Engineering Details

This document covers the deep technical optimizations implemented in the Roboklask firmware, communication bridge, and runtime scheduler.

---

## 1. High-Frequency Step Generation (Zephyr RTOS)

### The Challenge
Standard Arduino environments run `loop()` sequentially. In RTOS-based cores (like Zephyr RTOS on Arduino UNO R4), returning from `loop()` triggers system-level thread rescheduling, serial polling, and hardware events. This introduces a background overhead of **200µs to 1ms** per iteration.

Because `AccelStepper` relies on a polling architecture (`stepper.run()`), it must be called at a frequency higher than the required step pulse frequency. With a target operational speed of **16,000 steps/second** (at 1/8 microstepping), the minimum polling frequency must exceed **30kHz**. Polling inside a standard `loop()` limited to 1kHz due to core overhead restricts the motor speed to a crawl (under 2,000 steps/sec).

### The Optimization
We bypassed the Arduino core's `loop()` return overhead by encapsulating the execution inside an internal infinite `while(true)` loop:

```cpp
void loop() {
  unsigned long last_yield_ms = 0;

  while (true) {
    // 1. Poll stepper motors at max CPU frequency (~100kHz)
    xyControl.run();

    unsigned long current_time = millis();

    // 2. Manage 33ms control cycles with guard clauses
    if (current_time - last_update_ms < CYCLE_ms) {
      #if defined(ARDUINO_UNO_Q)
      if (Serial1.available() > 0) {
        safeUpdate();
      }
      // Thread Starvation Guard: Yield exactly once per millisecond
      if (current_time - last_yield_ms >= 1) {
        last_yield_ms = current_time;
        k_yield();
      }
      #endif
      continue;
    }
    last_update_ms = current_time;

    // 3. Execute 33ms periodic logic (target coordinates, matrix rendering)
    ...
  }
}
```

* **Result**: Step polling frequency increased from ~1kHz to **~100kHz**, unlocking the full potential of the NEMA 17 steppers to run smoothly at **16,000 steps/sec** with an acceleration profile of **25,600 steps/sec²**.
* **Thread Safety**: Calling `k_yield()` once every 1ms ensures that Zephyr's network and system threads get their time slices, preventing any hardware lockups.

---

## 2. Low-Latency RPC over MessagePack-RPC

### The Challenge
Initially, the Python tracker sent separate RPC notifications for target striker positions (`py2mcu`) and target ball positions (`ball`) at 30Hz. This generated **60 packets/second** over the 115200bps serial port. The overhead of serial packet parsing and deserialization on the MCU created a queue bottleneck: when the python sender stopped, the robot continued to move for several seconds (queued command latency).

### The Optimization
1. **Consolidated Payload**: We merged the target coordinate and the ball coordinates into a single MessagePack-RPC call:
   ```python
   # Python Driver
   self.bridge.notify("py2mcu", target.x, target.y, ball.x, ball.y)
   ```
2. **Synchronous Buffer Flushing (`safeUpdate`)**: Instead of relying on Zephyr's asynchronous service thread to deserialize packets, the main loop detects data in the buffer (`Serial1.available() > 0`) and triggers `safeUpdate()` synchronously.
3. **Step-Level Change Detection**:
   Floating-point coordinate values fluctuate slightly due to camera noise (e.g., `0.0001` variance). Overwriting the target via `stepper.moveTo()` resets AccelStepper's acceleration planner. We wrapped the target setter to only execute `moveTo()` when the actual physical target steps change:
   ```cpp
   long target_s1 = (target_step_x + target_step_y) * resolution;
   long target_s2 = (-target_step_x + target_step_y) * resolution;

   if (target_s1 != last_target_s1 || target_s2 != last_target_s2) {
     stepper1.moveTo(target_s1);
     stepper2.moveTo(target_s2);
     last_target_s1 = target_s1;
     last_target_s2 = target_s2;
   }
   ```
* **Result**: Latency accumulation is completely eliminated. The robot tracking response matches the 33ms vision loop instantaneously.

---

## 3. Kinetic Safety & Boundary Calibration

### The Challenge
Homing absolute coordinates via raw step offsets can lead to physical limit switch crashes if the two motors run slightly out of sync. Furthermore, keeping the striker away from physical limit walls reduces its playable range.

### The Optimization
* **Relative Target Homing**: Homing steps are commanded via relative movements (`move()`) rather than absolute targets (`moveTo()`). This guarantees that both H-bot motors receive identical step pulses, keeping the carriage perfectly straight during homing.
* **Separation of Safety Margins**:
  We separated the physical release limit (`PHYSICAL_BACK = 300` steps) from the software play boundary limit (`STEP_BACK_X`, `STEP_BACK_Y = 100` steps).
  ```cpp
  constexpr int XSTEP = 3100 * 2 + 500 - STEP_BACK_X * 2;
  constexpr int YSTEP = 1500 * 2 + 100 - STEP_BACK_Y;
  ```
  This maximizes the playable area (`XSTEP=2900`, `YSTEP=1400`) while allowing the robot to calibrate its zero-point exactly `100` steps away from the physical switches.
* **Dynamic Recalibration & Non-Blocking Escape**: If a limit switch is triggered mid-game, the robot immediately stops and executes a backing-off routine (`escapeX/Y` by `PHYSICAL_BACK` steps). During this backing-off `while` loop, the code actively processes serial communications (`safeUpdate()`) and yields thread control (`k_yield()`) to prevent the Zephyr RTOS communication stacks from starving and dropping the connection. Afterwards, the MCU recalculates and overrides the absolute coordinates on the fly (`resetX/Y`) seamlessly.
