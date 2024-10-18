"""
このスクリプトは、入力されたJSONLファイル内のUnicodeエスケープシーケンスを元のテキストに変換し、
指定された出力ファイルに書き込むか、コンソールに出力するためのものです。
"""

import json

def convert_unicode_to_text(input_file, output_file=None):
    """
    JSONLファイル内のUnicodeエスケープシーケンスを元のテキストに変換し、出力する関数。
    
    パラメータ:
    - input_file: 入力JSONLファイルのパス
    - output_file: 出力ファイルのパス（Noneの場合はコンソールに出力）
    """
    # JSONLファイルを読み込む
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # JSONLファイルの各行をパースし、Unicodeエスケープシーケンスを変換
    data = [json.loads(line) for line in lines]

    if output_file:
        # 変換後のデータを指定された出力ファイルに書き込む
        with open(output_file, 'w', encoding='utf-8') as f:
            for item in data:
                f.write(f"Input: {item['input']}\n")
                f.write(f"Prediction: {item['pred']}\n")
                f.write(f"Label: {item['label']}\n\n")
    else:
        # 変換後のデータをコンソールに出力
        for item in data:
            print("Input:", item['input'])
            print("Prediction:", item['pred'])
            print("Label:", item['label'])
            print()

# 使用例
input_file = '/workspace/results/elyza_7b_ptuning_test_jcommonsenseqa-v1.1_inputs_preds_labels.jsonl'
output_file = '/workspace/output/elyza_7b_ptuning_test_jcommonsenseqa-v1.1_inputs_preds_labels.txt'  # または出力ファイルパスを指定 (例: 'output.txt')
convert_unicode_to_text(input_file, output_file)
