"""
このスクリプトは、入力されたJSONL形式のデータを読み込み、タイトルや本文に基づいてプロンプトを生成し、
それをトレーニング、検証、およびテストデータセットに分割してJSONL形式で保存します。
"""

import json
import os
import random
import re

# 入力ファイルと出力ディレクトリのパスを指定
INPUT_FILE = "/workspace/data/mydata/split_curator/3_decontamination_pro/processed_pro.jsonl"
OUTPUT_DIR = "/workspace/data/nemo_peft_pro_processed_data_split_curator"

# JSONLファイルに書き出す関数
def write_jsonl(fname, json_objs):
    """
    JSONL形式でデータをファイルに書き出す関数。

    パラメータ:
    - fname: 出力ファイルのパス
    - json_objs: JSONオブジェクトのリスト
    """
    with open(fname, 'wt', encoding='utf-8') as f:
        for o in json_objs:
            f.write(json.dumps(o, ensure_ascii=False) + "\n")

# タイトルが意味のあるものであるかを判定する関数
def is_meaningful_title(title):
    """
    タイトルが意味のある内容かどうかを判定する。

    パラメータ:
    - title: タイトル文字列

    戻り値:
    - タイトルが無意味な数字や拡張子でない場合はTrue、そうでない場合はFalse
    """
    return not re.match(r'^[\d\s]*$', title) and not title.lower().endswith(('.pdf', '.doc', '.txt'))

# テキストから質問を抽出する関数
def extract_question_from_text(text, max_length=50):
    """
    テキストから最初の質問を抽出し、最大長50文字に制限する。

    パラメータ:
    - text: テキスト文字列
    - max_length: 質問の最大長（デフォルトは50）

    戻り値:
    - 抽出された質問文
    """
    sentences = re.split(r'[。！？\n]', text)
    question = ""
    for sentence in sentences:
        sentence = sentence.strip()
        if sentence and len(question) + len(sentence) <= max_length:
            question += sentence + "。"
        if len(question) >= max_length:
            break
    return question.strip()

# プロンプトを生成する関数
def form_prompt(title, text):
    """
    タイトルとテキストに基づいてプロンプトを生成する。

    パラメータ:
    - title: タイトル文字列
    - text: テキスト文字列

    戻り値:
    - 生成されたプロンプト
    """
    if is_meaningful_title(title):
        # タイトルが意味のある場合、複数のプロンプト候補からランダムに選択
        prompts = [
            f"「{title}」について要約してください。",
            f"{title}に関する主要な情報を3点挙げてください。",
            f"{title}の内容を、新入生向けに分かりやすく説明してください。",
            f"{title}に関連する大学生活のアドバイスを提供してください。",
            f"{title}の情報を基に、大学のPRポイントを挙げてください。"
        ]
        return random.choice(prompts)
    else:
        # タイトルが意味のない場合、テキストから質問を生成
        question = extract_question_from_text(text)
        if question:
            return f"次の文章に基づいて質問に答えてください：「{question}」"
        else:
            return "この文書の内容を要約してください。"

# データを処理してトレーニング、検証、テストセットに分割する関数
def process(input_path):
    """
    JSONLファイルを読み込み、プロンプトを生成し、データをトレーニング、検証、テストセットに分割して保存する。

    パラメータ:
    - input_path: 入力JSONLファイルのパス
    """
    # JSONLファイルを読み込む
    with open(input_path, encoding='utf-8') as f:
        dataset = [json.loads(line) for line in f]

    processed = []
    # 各データについてプロンプトを生成
    for data in dataset:
        prompt = form_prompt(data['title'], data['text'])
        processed.append({"input": prompt, "output": data['text']})

    # データセットをシャッフルして、トレーニング、検証、テストセットに分割
    random.shuffle(processed)
    train_size = int(len(processed) * 0.8)  # トレーニングセット：80%
    valid_size = int(len(processed) * 0.1)  # 検証セット：10%

    train_ds = processed[:train_size]
    valid_ds = processed[train_size:train_size + valid_size]
    test_ds = processed[train_size + valid_size:]

    # 各データセットをJSONLファイルに書き出す
    write_jsonl(f"{OUTPUT_DIR}/train.jsonl", train_ds)
    write_jsonl(f"{OUTPUT_DIR}/valid.jsonl", valid_ds)
    write_jsonl(f"{OUTPUT_DIR}/test.jsonl", test_ds)

# メイン関数
def main():
    """
    メイン処理。出力ディレクトリを作成し、データを処理。
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    process(INPUT_FILE)
    print(f"Processing complete. Output saved to {OUTPUT_DIR}")

# スクリプトが直接実行された場合、メイン関数を呼び出す
if __name__ == "__main__":
    main()
