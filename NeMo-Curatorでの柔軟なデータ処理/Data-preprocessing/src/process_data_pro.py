'''
このスクリプトは、入力されたJSONLファイルのデータを処理し、テキストをクリーニングした後、指定された最大長に従ってテキストを分割します。
処理済みデータは新しいJSONファイルに出力されます。

使用例:
python /workspace/src/process_data_pro.py \
    /workspace/data/raw_data/data.jsonl \
    /workspace/data/mydata/split_curator/0_processed_pro/processed_pro.json
'''

import json
import sys
import re

# テキストをクリーニングする関数
def clean_text(text):
    """
    テキスト内の特殊文字や不要な部分を削除し、クリーニングを行う。

    処理内容:
    - 改行文字の統一（\r -> \n）
    - HTMLタグの削除
    - 連続する空白を1つの空白に置換（段落間の改行は保持）
    - URLの削除
    - 日本語と標準的な句読点、空白以外の特殊文字を削除
    - 行の先頭と末尾の空白を削除

    パラメータ:
    - text: 処理対象のテキスト

    戻り値:
    - クリーニング済みのテキスト
    """
    # \rを\nに置換
    text = text.replace('\r', '\n')
    # HTMLタグを削除
    text = re.sub(r'<[^>]+>', '', text)
    # 連続する空白やタブ、改行を正規化
    text = re.sub(r'\s*\n\s*', '\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    # URLを削除
    text = re.sub(r'https?://\S+', '', text)
    # 特殊文字の削除（日本語と句読点を残す）
    text = re.sub(r'[^\w\s\.\,\?\!。、？！（）｢｣「」ぁ-んァ-ン一-龥 ]', '', text)
    # 各行の先頭と末尾の空白を削除
    text = '\n'.join(line.strip() for line in text.split('\n'))
    return text.strip()

# テキストを最大長に従って分割する関数
def split_text(data, max_length=300):
    """
    テキストを指定された最大長に従って分割し、各セクションをリストとして返す。

    パラメータ:
    - data: 入力データ（タイトル、テキスト、URLを含む）
    - max_length: 分割の基準となるテキストの最大長

    戻り値:
    - 分割されたデータのリスト
    """
    result = []
    # タイトルとテキストをクリーニング
    title = clean_text(data['title'])
    url = data['url']
    text = clean_text(data['text'])

    # テキストが最大長以下であれば、そのまま追加
    if len(text) <= max_length:
        result.append({
            'title': title,
            'text': text,
            'url': url
        })
        return result

    # 文章を句読点や改行で分割
    sentences = re.split(r'([。！？\n])', text)
    # 分割された句と区切り文字を結合
    sentences = [''.join(i) for i in zip(sentences[0::2], sentences[1::2])]

    # 分割されたテキストをまとめる
    current_chunk = ""
    for sentence in sentences:
        if len(current_chunk) + len(sentence) <= max_length:
            current_chunk += sentence
        else:
            # 現在のチャンクを結果に追加
            if current_chunk:
                result.append({
                    'title': title,
                    'text': current_chunk.strip(),
                    'url': url
                })
            current_chunk = sentence

    # 最後のチャンクを追加
    if current_chunk:
        result.append({
            'title': title,
            'text': current_chunk.strip(),
            'url': url
        })
    
    return result

# JSONLファイルを処理して出力ファイルに書き込む関数
def process_jsonl(input_file, output_file):
    """
    入力されたJSONLファイルを処理し、テキストを分割・クリーニングした後、出力ファイルに保存する。

    パラメータ:
    - input_file: 入力JSONLファイルのパス
    - output_file: 出力ファイルのパス
    """
    with open(input_file, 'r', encoding='utf-8') as infile, \
         open(output_file, 'w', encoding='utf-8') as outfile:
        for line in infile:
            try:
                # 各行のJSONデータを読み込む
                data = json.loads(line.strip())
                # テキストを分割する
                split_data = split_text(data)
                # 分割されたデータを出力ファイルに書き込む
                for item in split_data:
                    json.dump(item, outfile, ensure_ascii=False)
                    outfile.write('\n')
            except json.JSONDecodeError:
                print(f"JSONデコードエラー: {line}")
            except KeyError as e:
                print(f"データにキーがありません: {e}")

# メイン関数
if __name__ == "__main__":
    # コマンドライン引数の数をチェック
    if len(sys.argv) != 3:
        print("使用方法: python process_data_pro.py <input_file> <output_file>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    # JSONLデータの処理を実行
    process_jsonl(input_file, output_file)
    print(f"処理完了。出力ファイル: {output_file}")
