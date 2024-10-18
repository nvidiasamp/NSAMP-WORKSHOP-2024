"""
このスクリプトは、入力されたJSONLファイル内のUnicodeエスケープシーケンスを元のテキストに変換し、
変換後のデータを新しいJSONLファイルとして出力するためのものです。
"""

import json

def convert_unicode_jsonl(input_file, output_file):
    """
    JSONLファイル内のUnicodeエスケープシーケンスを元のテキストに変換し、新しいJSONLファイルに書き込む関数。

    パラメータ:
    - input_file: 入力JSONLファイルのパス
    - output_file: 出力JSONLファイルのパス
    """
    # JSONLファイルを読み込む
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # JSONLファイルの各行をパースし、Unicodeエスケープシーケンスを変換
    data = [json.loads(line) for line in lines]

    # 変換後のデータを新しいJSONLファイルに書き込む
    with open(output_file, 'w', encoding='utf-8') as f:
        for item in data:
            # ensure_ascii=Falseにより、Unicode文字がエスケープされないようにする
            json.dump(item, f, ensure_ascii=False)
            f.write('\n')

# 使用例
input_file = '/workspace/results/elyza_7b_ptuning_test_jcommonsenseqa-v1.1_inputs_preds_labels.jsonl'
output_file = '/workspace/output/elyza_7b_ptuning_test_jcommonsenseqa-v1.1_inputs_preds_labels_text.jsonl'
convert_unicode_jsonl(input_file, output_file)
