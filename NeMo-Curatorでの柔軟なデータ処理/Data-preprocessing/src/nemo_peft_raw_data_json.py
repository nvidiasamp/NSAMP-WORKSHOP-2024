"""
このスクリプトは、指定されたJSONL形式の生データを読み込み、タイトルに基づいてプロンプトを生成し、
トレーニング、検証、およびテストデータセットに分割してJSONL形式で保存します。
"""

import json
import os
import random

# 原データのパス（デフォルト）
INPUT_FILE = "/workspace/data/raw_data/data.jsonl"
OUTPUT_DIR = "/workspace/data/nemo_peft_raw_data_default"

# rawデータを分割する場合
# INPUT_FILE = "/workspace/data/raw_data/split_raw_data.jsonl"
# OUTPUT_DIR = "/workspace/data/nemo_peft_raw_data_edit_len"

# 分割後にnemo-curatorで前処理を行う場合
# INPUT_FILE = "/workspace/data/mydata/split_curator/3_decontamination/processed_data.jsonl"
# OUTPUT_DIR = "/workspace/data/nemo_peft_processed_data_split_curator"

# 前処理後に分割を行う場合
# INPUT_FILE = "/workspace/data/mydata/curator_split"
# OUTPUT_DIR = "/workspace/data/nemo_peft_processed_data_curator_split"

# JSONLファイルにデータを書き出す関数
def write_jsonl(fname, json_objs):
    """
    JSONL形式でデータをファイルに書き出す関数。

    パラメータ:
    - fname: 出力ファイルのパス
    - json_objs: JSONオブジェクトのリスト
    """
    with open(fname, 'wt') as f:
        for o in json_objs:
            f.write(json.dumps(o, ensure_ascii=False) + "\n")

# タイトルに基づいてプロンプトを生成する関数
def form_prompt(title):
    """
    タイトルに基づいてブログ記事生成用のプロンプトを作成する。

    パラメータ:
    - title: タイトル文字列

    戻り値:
    - 生成されたプロンプトの文字列
    """
    st = "### 指示:\n"
    st += "以下のタイトルに基づいて、適切なブログ記事の本文を生成してください。\n"
    st += "### 入力:\n"
    st += f"{title}\n"
    st += "### 応答:"
    return st

# データを処理してトレーニング、検証、テストセットに分割する関数
def process(input_path):
    """
    JSONLファイルを読み込み、プロンプトを生成し、データをトレーニング、検証、テストセットに分割して保存する。

    パラメータ:
    - input_path: 入力JSONLファイルのパス
    """
    # JSONLファイルを読み込む
    with open(input_path) as f:
        dataset = [json.loads(line) for line in f]

    processed = []
    # 各データに対してプロンプトを生成し、処理済みリストに追加
    for data in dataset:
        prompt = form_prompt(data['title'])
        processed.append({"input": prompt, "output": data['text']})

    # データをシャッフルし、トレーニング、検証、テストセットに分割
    random.shuffle(processed)
    train_size = int(len(processed) * 0.8)  # トレーニングセットのサイズ（80%）
    valid_size = int(len(processed) * 0.1)  # 検証セットのサイズ（10%）

    train_ds = processed[:train_size]
    valid_ds = processed[train_size:train_size + valid_size]
    test_ds = processed[train_size + valid_size:]

    # 各データセットをJSONLファイルに書き出し
    write_jsonl(f"{OUTPUT_DIR}/train.jsonl", train_ds)
    write_jsonl(f"{OUTPUT_DIR}/valid.jsonl", valid_ds)
    write_jsonl(f"{OUTPUT_DIR}/test.jsonl", test_ds)

# メイン関数
def main():
    """
    メイン処理。データを処理し、トレーニング、検証、テストデータに分割。
    """
    process(INPUT_FILE)

# スクリプトが直接実行された場合、メイン関数を呼び出す
if __name__ == "__main__":
    main()
