# SKILL: Arduino UNO Q デバイス概要

## デバイスの概要
**Arduino UNO Q**は、高レベルな処理を担うLinuxマイクロプロセッサ（MPU）と、リアルタイム制御を担うArduinoマイクロコントローラ（MCU）を1つのボードに統合したシングルボードコンピュータです。このデュアルアーキテクチャプラットフォームにより、AIエッジアプリケーションなどに必要な高性能コンピューティングと、決定論的なリアルタイムハードウェア制御を同時に実現します。両プロセッサ間は、内蔵のRPCライブラリ（Arduino Bridge）とバックグラウンドで稼働する `arduino-router` デーモンによってシームレスに連携しています。

## プロセッサ (MPU / MCU)
UNO Qは、それぞれ以下の高性能な専用プロセッサを搭載しています。

*   **MPU (Microprocessor Unit)**: **Qualcomm Dragonwing™ QRB2210**
    *   **仕様**: Quad-core Arm® Cortex®-A53 (2.0 GHz)。
    *   **特徴**: Adreno GPU 3Dグラフィックスアクセラレータ、デュアルISP (13 MP + 13 MP または 25 MP @ 30 fps) などを備えています。主にPythonアプリケーション、AIモデル、高度なロジック処理を担います。
*   **MCU (Microcontroller Unit)**: **STMicroelectronics STM32U585**
    *   **仕様**: 32-bit Arm® Cortex®-M33 (最大 160 MHz)。
    *   **特徴**: 2 MBのフラッシュメモリ、786 kBのSRAM、浮動小数点演算ユニット（FPU）を搭載しています。センサーからのデータ読み取りやモーター制御など、リアルタイムなArduinoスケッチ（C++）を遅延なく実行します。

## オペレーティングシステム (OS)
*   **MPU側 (Linux)**: **Debian Linux OS**。
    MPU上では、アップストリームサポートを備えた**完全なDebianベースのLinux環境**が組み込まれて稼働しています。開発者は馴染みのあるLinux環境でそのまま開発を行うことが可能であり、スタンドアロンのPCのようにも扱えます。
    *※注意: ソース文献内では単に「Debian Linux」とのみ記載されており、ご指定の「Debian 13」という具体的なメジャーバージョンについては言及されていません。*
*   **MCU側 (Arduino / Zephyr)**: **Zephyr OS**。
    MCU側にデプロイされるArduinoスケッチは、**リアルタイムOSであるZephyr OS上で動作**します。これにより、クリティカルなタイミングが要求される処理を確実に実行できます。

## References
*   [UNO Q | Arduino Documentation](https://docs.arduino.cc/hardware/uno-q)
*   [Working with Arduino Router RPC | Arduino Documentation](https://docs.arduino.cc/tutorials/uno-q/routerbridge-multilanguage/)
