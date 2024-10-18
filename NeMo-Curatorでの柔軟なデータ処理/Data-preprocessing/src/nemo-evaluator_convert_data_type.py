'''
このスクリプトは、前処理済みデータと生データを特定の形式に変換し、JSONファイルとして保存します。
それぞれのデータは、NeMo評価ツールで使用される形式に変換されます。

使用方法:
cd workspace

python src/nemo-evaluator_convert_data_type.py \
    /path/to/preprocessed_file.jsonl \
    /path/to/raw_file.jsonl \
    /path/to/converted_preprocessed_file.json \
    /path/to/converted_raw_file.json

例.)
python src/nemo-evaluator_convert_data_type.py \
    /workspace/data/jcommonsenseqa-v1.1/train-v1.1.jsonl \
    /workspace/JGLUE/datasets/jcommonsenseqa-v1.1/train-v1.1.json \
    /workspace/data/nemo-evaluator/converted_preprocessed_file.json \
    /workspace/data/nemo-evaluator/converted_raw_file.json
'''

import json
import sys

# 前処理済みデータを変換する関数
def convert_preprocessed_data(data):
    """
    前処理済みデータを変換し、新しい形式に変換する。

    パラメータ:
    - data: 前処理されたデータ

    戻り値:
    - 変換されたデータの辞書
    """
    return {
        "prompt": data["input"],  # 'input'としてプロンプトを格納
        "ideal_response": data["output"],  # 'output'として理想的な応答を格納
        "category": "Multiple Choice"  # カテゴリを"Multiple Choice"に設定
    }

# 生データを変換する関数
def convert_raw_data(data):
    """
    生データを変換し、新しい形式に変換する。

    パラメータ:
    - data: 生データ

    戻り値:
    - 変換されたデータの辞書
    """
    # 選択肢を配列として格納
    choices = [data["choice0"], data["choice1"], data["choice2"], data["choice3"], data["choice4"]]
    # プロンプトに質問と選択肢をフォーマットして格納
    prompt = f"{data['question']}\n選択肢:\n" + "\n".join([f"- {choice}" for choice in choices])
    
    return {
        "prompt": prompt,  # プロンプトを格納
        "ideal_response": choices[data["label"]],  # 正しい選択肢を格納
        "category": "Multiple Choice",  # カテゴリを"Multiple Choice"に設定
        "choices": choices,  # 選択肢のリストを格納
        "q_id": data["q_id"]  # 質問IDを格納
    }

# メイン関数
def main(preprocessed_file, raw_file, converted_preprocessed_file, converted_raw_file):
    """
    前処理済みデータと生データを読み込み、それぞれを変換してJSONファイルに保存する。

    パラメータ:
    - preprocessed_file: 前処理済みデータのファイルパス
    - raw_file: 生データのファイルパス
    - converted_preprocessed_file: 変換された前処理済みデータの保存先ファイルパス
    - converted_raw_file: 変換された生データの保存先ファイルパス
    """
    # 前処理済みデータの読み込みと変換
    converted_preprocessed = []
    with open(preprocessed_file, 'r', encoding='utf-8') as f:
        for line in f:
            data = json.loads(line.strip())
            converted_preprocessed.append(convert_preprocessed_data(data))

    # 生データの読み込みと変換
    converted_raw = []
    with open(raw_file, 'r', encoding='utf-8') as f:
        for line in f:
            data = json.loads(line.strip())
            converted_raw.append(convert_raw_data(data))

    # 変換された前処理済みデータの保存
    with open(converted_preprocessed_file, 'w', encoding='utf-8') as f:
        json.dump(converted_preprocessed, f, ensure_ascii=False, indent=2)

    # 変換された生データの保存
    with open(converted_raw_file, 'w', encoding='utf-8') as f:
        json.dump(converted_raw, f, ensure_ascii=False, indent=2)

# コマンドラインからの引数が正しいか確認し、メイン関数を実行
if __name__ == '__main__':
    if len(sys.argv) != 5:
        print("Usage: python script.py <preprocessed_file> <raw_file> <converted_preprocessed_file> <converted_raw_file>")
        sys.exit(1)

    # コマンドライン引数を取得
    preprocessed_file = sys.argv[1]
    raw_file = sys.argv[2]
    converted_preprocessed_file = sys.argv[3]
    converted_raw_file = sys.argv[4]
    
    # メイン関数を実行
    main(preprocessed_file, raw_file, converted_preprocessed_file, converted_raw_file)
