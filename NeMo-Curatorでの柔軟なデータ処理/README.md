# NeMo-Curatorでの柔軟なデータ処理

## プロジェクト概要

URLからデータをスクレイピングし、さらに分析やモデルトレーニングのために前処理を行うための完全なパイプラインを提供します。本プロジェクトは、データのスクレイピングとデータの前処理という2つの主要な部分で構成されています。

## ディレクトリ構成

- **[Data-scraping](./Data-scraping)**: データスクレイピングモジュール。URLからデータをスクレイピングするためのスクリプトやツールを含んでいます。[詳細説明はこちら](./Data-scraping/README.md)
  
- **[Data-preprocessing](./Data-preprocessing)**: データ前処理モジュール。データのクリーニング、変換、および準備を行うスクリプトを含んでいます。[詳細説明はこちら](./Data-preprocessing/README.md)

## 使用方法

1. **データスクレイピング**: 最初に`Data-scraping`ディレクトリ内のREADMEを参照し、スクレイピングツールの設定と使用方法を確認してください。
2. **データ前処理**: データのスクレイピングが完了したら、`Data-preprocessing`ディレクトリ内のREADMEを参照し、データの前処理操作を行ってください。

## 実行環境と実験環境

- Python 3.x
- Docker
- GPU：NVIDIA RTX 6000 Ada Generation 48 GB x 1
- オペレーティングシステム：Ubuntu 20.04.6 LTS
