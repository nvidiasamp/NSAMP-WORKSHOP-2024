"""
このスクリプトは、与えられたJSON形式のデータを読み込み、指定されたフォーマットでプロンプトと応答を生成し、
それをJSONL形式で出力するためのものです。トレーニングデータの場合は、データをシャッフルして
トレーニングセットと検証セットに分割します。主に、大規模言語モデルの学習に使用するデータセットの
前処理に利用されます。
"""

import json
import os
import random
 
# 入力ファイルと出力ディレクトリのパスを指定
INPUT_TRAIN = ""  # トレーニングデータの入力ファイル
INPUT_VALID = ""  # 検証データの入力ファイル
OUTPUT_DIR = "./data/mydata"  # 出力されるデータの保存ディレクトリ
 
# 乱数シードを固定することで結果の再現性を確保
random.seed(42)
# 出力ディレクトリを作成。既に存在する場合は何もしない
os.makedirs(OUTPUT_DIR, exist_ok=True)
 
# JSON Lines形式でファイルに書き出す関数
def write_jsonl(fname, json_objs):
    """
    json_objsに含まれるオブジェクトをJSONL形式でファイルに書き出す。
    
    Parameters:
    fname (str): 出力ファイルのパス
    json_objs (list): JSONオブジェクトのリスト
    """
    with open(fname, 'wt') as f:
        # json_objsの各オブジェクトを1行ごとに書き込む
        for o in json_objs:
            f.write(json.dumps(o, ensure_ascii=False) + "\n")
 
# データセットの1つのオブジェクトをフォーマットし、指示や入力を含むプロンプトを作成
def form_data(obj):
    """
    1つのデータオブジェクトからプロンプトを作成する。
    
    Parameters:
    obj (dict): データオブジェクト
    
    Returns:
    str: プロンプトとして使用するテキスト
    """
    st = ""
    st += "### 指示:\n"
    st += "与えられた選択肢の中から、最適な答えを選んでください。出力は以下から選択してください：\n"
    st += f"- {obj['test']}\n"  # 選択肢の1つとして'test'を追加
    st += f"- {obj['url']}\n"   # 選択肢の1つとして'url'を追加
    st += "### 入力:\n"
    st += f"{obj['title']}\n"  # 'title'フィールドを入力データとして追加
    st += "### 応答:"
    return st
 
# データの処理を行う関数
# input_path: 入力データファイルのパス
# train: Trueの場合、データをトレーニングと検証に分割
def prosess(input_path, train=False):
    """
    指定されたデータファイルを読み込み、プロンプトと応答を含む形式に変換し、JSONLファイルとして出力する。
    
    Parameters:
    input_path (str): 入力データファイルのパス
    train (bool): トレーニング用データかどうか。Trueの場合、データをトレーニングと検証に分割。
    """
    # 入力ファイルを読み込み、各行をJSON形式でロードする
    with open(input_path) as f:
        dataset = [json.loads(line) for line in f.readlines()]
 
    processed = []
    # 各データを処理
    for data in dataset:
        # プロンプトを作成
        prompt = form_data(data)
        # 正しい答えを取得
        answer = data[f"choice{data['label']}"]
        # 'input'と'output'として保存
        processed.append({"input": prompt, "output": f"{answer}"})

    # トレーニングデータの場合、シャッフルしてトレーニングと検証に分割
    if train:
        random.shuffle(processed)
        train_ds = processed[:-1000]  # トレーニングデータ
        valid_ds = processed[-1000:]  # 検証データ
        # トレーニングと検証データをJSONLファイルとして保存
        write_jsonl(f"{OUTPUT_DIR}/train-v1.1.jsonl", train_ds)
        write_jsonl(f"{OUTPUT_DIR}/valid-v1.1.jsonl", valid_ds)
    else:
        # テストデータをJSONLファイルとして保存
        write_jsonl(f"{OUTPUT_DIR}/test-v1.1.jsonl", processed)
 
    return
 
# メイン関数
def main():
    """
    トレーニングデータと検証データの処理を行うメイン関数。
    """
    # トレーニングデータと検証データを処理
    prosess(INPUT_TRAIN, train=True)
    prosess(INPUT_VALID)
 
# スクリプトが直接実行された場合、メイン関数を呼び出す
if __name__ == "__main__":
    main()
