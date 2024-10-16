
# データ前処理パイプライン

## プロジェクト概要

このプロジェクトは、NVIDIAのNeMo-Curatorツールを使用して、URLからスクレイピングされたデータを前処理することを目的としています。特定の操作環境とデータ処理のニーズに合わせて、NeMo-Curatorに必要なカスタマイズを行いました。

![データ処理のフロー](https://github.com/nvidiasamp/5min_RAG/blob/shunmei/Data-preprocessing/NeMo-Curator.png)
*画像の出典 [NeMo-Curator GitHub リポジトリ](https://github.com/NVIDIA/NeMo-Curator)*

## ディレクトリ構成

- **NeMoCurator**: URLからスクレイピングされたデータを処理し、クリーンアップするためにカスタマイズされたNeMo-Curatorツール。
- **src**: 生データに対して特定の前処理操作を行うためのデータ処理スクリプトを含むディレクトリ。

## 環境準備

### 1. NeMo Frameworkコンテナの取得

NGCから最新のNeMo Frameworkコンテナを取得します：

```bash
docker pull nvcr.io/nvidia/nemo:24.03.01.framework
```

### 2. システム環境の設定

実験環境：

- オペレーティングシステム：Ubuntu 20.04.6 LTS
- GPU：NVIDIA RTX 6000 Ada Generation 48 GB x 1

### 3. 作業ディレクトリの作成

以下のコマンドを使用して作業ディレクトリを作成し、移動します：

```bash
mkdir <name>
cd <name>
```

## Dockerコンテナの起動

以下のコマンドを使用して設定済みのDockerコンテナを起動します：

```bash
cd <where>

docker run \
   --rm \
   -it \
   --name=<name> \
   --gpus device=0 \
   --shm-size=2g \
   --ulimit memlock=-1 \
   --network=host \
   -v ${PWD}:/workspace \
   -w /workspace \
   -v ${PWD}/results:/workspace/results \
   nvcr.io/nvidia/nemo:24.03.01.framework \
   bash
```

## NeMo-Curatorのカスタマイズと使用

### 1. NeMo-Curatorのクローン

まず、[NVIDIAのNeMo-Curatorリポジトリ](https://github.com/NVIDIA/NeMo-Curator.git)をクローンします：

```bash
git clone https://github.com/NVIDIA/NeMo-Curator.git
```

### 2. 必要なファイルの編集と保存

プロジェクトの要件に従って、次のファイルを編集し、保存します：

- `config/fasttext_langid.yaml`
- `example/edit_identify_languages_and_fix_unicode.py`
- `example/exact_deduplication.py`
- `example/task_decontamination.py`

### 3. ファイルパスと環境の調整

操作環境に応じてファイルパスを修正し、設定を保存します。

### 4. モデルのダウンロードと使用

このプロジェクトを使用する際は、[FastText公式サイト](https://fasttext.cc/)からFastTextモデルをダウンロードしてください。

また、テキストフォーマットの一貫性を確保するために、ftfyライブラリの使用を推奨します。詳細については[ftfyドキュメント](https://ftfy.readthedocs.io/en/latest/)を参照してください。

## データ処理スクリプト

特定の操作環境下で、生データの編集が必要になる場合があります。次のスクリプトを使用してデータの前処理を行います：

```bash
python src/process_data_pro.py
```

## 参考文献

本プロジェクトでは、関連するデータ処理およびツールのカスタマイズを行うために、以下のドキュメントを参考にしています：

- [言語識別とUnicodeフォーマット](https://github.com/NVIDIA/NeMo-Curator/blob/main/docs/user-guide/languageidentificationunicodeformatting.rst)
- [GPU重複排除処理](https://github.com/NVIDIA/NeMo-Curator/blob/main/docs/user-guide/gpudeduplication.rst)
- [タスクのデコンタミネーション処理](https://github.com/NVIDIA/NeMo-Curator/blob/main/docs/user-guide/taskdecontamination.rst)


