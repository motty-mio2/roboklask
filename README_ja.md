# 😀 roboklask

[English](./README.md) | 日本語

Arduino UNO R4 ファームウェアと Python ビジョンパイプラインによる、自動 Klask（クラスク）対戦ロボットのリポジトリです。

## リポジトリ構成

- **[`sketch/`](./sketch/)** — Arduino UNO R4 (UNO Q / Minima) 向けの C++ ファームウェア（2軸ステッピングモーター制御および通信ブリッジ）。
- **[`python/`](./python/)** — ビジョントラッキング（OAK-D / RealSense）、動作推論（強化学習 PPO / ボール追従）、Web UI を担当するコンパニオンアプリ。
- **[`hardware/`](./hardware/)** — 3Dプリント用メカ部品およびマウンタ設計。
  - **[ハードウェア＆3Dプリントガイド](./hardware/HardWare_ja.md)** ([English](./hardware/HardWare.md))

## ドキュメント

- **[ハードウェア＆3Dプリントガイド](./hardware/HardWare_ja.md)**: STLファイル一覧、BambuLab P1S 推奨印刷設定、各部品の詳細。
- **[Python パッケージドキュメント](./python/README.md)**: ビジョン追跡およびモーション制御アプリのセットアップと使い方。

