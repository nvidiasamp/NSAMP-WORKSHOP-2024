
# Data-scraping プロジェクト

## 概要

このプロジェクトは、指定されたソースから効率的にURLを収集し、データをダウンロードするためのものです。データのスクレイピング、処理、結果の整理された保存を構造化されたアプローチで提供します。

## プロジェクト構造

```
Data-scraping/
├── config/
│   └── config.yaml            # プロジェクトの実行に必要な設定が含まれた構成ファイル
├── data/
│   ├── output/                # スクレイピングと処理後のデータ結果を保存するディレクトリ
│   └── url/                   # 収集したURLリストを保存するディレクトリ
├── src/
│   ├── collect-urls-txt.py    # ウェブページからURLを収集するスクリプト
│   └── download_data.py       # URLからデータをダウンロードするスクリプト
├── Dockerfile                 # Dockerイメージを構築するためのファイル
└── requirements.txt           # Python依存パッケージのリスト
```

## 必要条件

- Python 3.x
- 必要なPythonパッケージは `requirements.txt` に記載されています。

## 構成

`config/config.yaml` ファイルには、スクリプトを効果的に実行するために必要なすべての設定が含まれています。主な設定は以下の通りです：

- **`headers`**: HTTP リクエストヘッダー情報、ネットワークリクエストに使用。
- **`timeout`**: リクエストのタイムアウト時間、リクエストがスタックしないようにするため。
- **`urls_directory`**: スクレイピングするURLリストを保存するディレクトリ。
- **`output_folder`**: スクレイピング結果を保存するディレクトリパス。
- **`output_filename`**: スクレイピング結果を保存するファイル名。
- **`log_filename`**: ログファイル名、スクレイピングプロセス中のログ情報を記録。
- **`max_workers`**: URLを並行してスクレイピングするための最大スレッド数。
- **`ignored_domains`**: スクレイピングしないドメインのリスト、これらのドメインのリンクは無視されます。

## 使用方法

1. **URLの収集 | URL収集**
   - 指定されたソースからURLを収集し、それらを `data/url` ディレクトリに保存するために `collect-urls-txt.py` スクリプトを実行します。

   ```bash
   python src/collect-urls-txt.py --config config/config.yaml
   ```

2. **データのダウンロード | データ取得**
   - 収集したURLからデータをダウンロードし、`data/output` ディレクトリに結果を保存するために `download_data.py` スクリプトを実行します。

   ```bash
   python src/download_data.py --config config/config.yaml
   ```

## ログ管理

ログは `data/output/scrape_log.log` ファイルに保存され、スクレイピングプロセスや発生した問題の追跡に使用されます。

## Docker Support

このプロジェクトを実行するためのコンテナ化された環境を作成するために `Dockerfile` が提供されています。以下のコマンドを使用してDockerイメージをビルドします：

```bash
docker build -t data-scraping-project .
```

次のコマンドを使用してDockerコンテナを実行します：

```bash
docker run -it --rm --name data-scraping-container data-scraping-project
```
