# Copyright (c) 2024, NVIDIA CORPORATION.  All rights reserved.
#
# Apache License 2.0の条件に基づき、本ファイルは使用されています。
# このコードのライセンスについては、下記のURLで確認できます。
# http://www.apache.org/licenses/LICENSE-2.0
#
# このスクリプトは、NeMo Curatorを使用して多言語データを処理し、特定の言語を識別・分離し、
# Unicodeの修正を行い、結果を保存するためのものです。

import argparse
import os
import logging

import ftfy  # テキストデータのUnicodeエラーを修正するライブラリ
import nemo_curator as nc  # NeMo Curatorモジュール
from nemo_curator.datasets import DocumentDataset  # データセットの読み込み
from nemo_curator.filters import FastTextLangId  # FastTextベースの言語識別フィルター
from nemo_curator.utils.distributed_utils import get_client, read_data, write_to_disk  # データの読み込みと書き出し
from nemo_curator.utils.file_utils import (
    get_all_files_paths_under,  # ディレクトリ内の全ファイルを取得
    separate_by_metadata,  # メタデータによる分割処理
)
from nemo_curator.utils.script_utils import ArgumentHelper  # スクリプト引数のヘルパー

# ログ設定：INFOレベルでログを出力
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# テキストのUnicodeエラーを修正する関数
def fix_unicode(text):
    """
    テキスト内のUnicodeエラーを修正し、修正が行われた場合はデバッグログに記録します。

    パラメータ:
    - text: 修正対象のテキスト

    戻り値:
    - 修正済みのテキスト
    """
    fixed = ftfy.fix_text(text)
    if fixed != text:
        logging.debug(f"Fixed Unicode: '{text}' -> '{fixed}'")
    return fixed

# データセットを読み込む関数
def load_dataset(input_data_dir):
    """
    指定されたディレクトリ内のファイルを読み込み、データセットとして返します。

    パラメータ:
    - input_data_dir: データセットのディレクトリ

    戻り値:
    - 読み込まれたデータセット
    """
    files = list(get_all_files_paths_under(input_data_dir))
    if not files:
        logging.warning(f"No files found in {input_data_dir}")
        return None
    logging.info(f"Found {len(files)} files in {input_data_dir}")
    raw_data = read_data(files, file_type="jsonl", backend="pandas", add_filename=True)
    dataset = DocumentDataset(raw_data)
    return dataset

# メイン処理
def main(args):
    """
    データセットの読み込み、言語識別、データの分離、Unicodeエラーの修正、およびクリーンデータの保存を行うメイン処理。

    パラメータ:
    - args: コマンドライン引数
    """
    # データとモデルのパス設定
    multilingual_data_path = "/workspace/data/mydata/split_curator/0_processed_pro"  # 多言語データ
    language_separated_output_path = "/workspace/data/mydata/split_curator/1_Language_Identification_pro"  # 言語分離後のデータ出力先
    cleaned_data_output_path = "/workspace/data/mydata/split_curator/1_cleaned_pro"  # クリーンデータの出力先
    model_path = "/workspace/models/Language_identification/lid.176.bin"  # 言語識別モデルのパス
    target_language = "JA"  # 対象言語 (ここでは日本語)
    language_field = "language"  # 言語フィールド

    # クライアント設定を読み込む
    client = get_client(**ArgumentHelper.parse_client_args(args))

    # データセットの読み込み
    multilingual_dataset = load_dataset(multilingual_data_path)
    if multilingual_dataset is None:
        logging.error("Failed to load dataset. Exiting.")
        return

    # FastText言語識別フィルターを設定してデータに適用
    language_id_pipeline = nc.ScoreFilter(
        FastTextLangId(model_path), score_field=language_field, score_type="object"
    )
    filtered_dataset = language_id_pipeline(multilingual_dataset)

    # 言語スコアを除去して日本語データに限定
    filtered_dataset.df[language_field] = filtered_dataset.df[language_field].apply(
        lambda score: score[1], meta=(None, str)
    )

    # 言語ごとにデータセットを分割
    try:
        language_stats = separate_by_metadata(
            filtered_dataset.df,
            language_separated_output_path,
            metadata_field=language_field,
        ).compute()
        logging.info(f"Language statistics: {language_stats}")
    except Exception as e:
        logging.error(f"Error while separating metadata: {e}")
        return

    # 言語ごとのデータを読み込み、Unicodeエラーを修正
    lang_data_path = os.path.join(language_separated_output_path, target_language)
    if not os.path.exists(lang_data_path):
        logging.error(f"Dataset did not have language: {target_language}")
        return
    lang_data = load_dataset(lang_data_path)
    if lang_data is None:
        logging.error(f"Failed to load language-specific data for {target_language}")
        return

    # テキストのUnicode修正を適用
    lang_data.df['text'] = lang_data.df['text'].apply(fix_unicode)

    # クリーンデータをファイルに書き出す
    try:
        write_to_disk(lang_data.df, cleaned_data_output_path, write_to_filename=True)
        logging.info(f"Cleaned data written to {cleaned_data_output_path}")
    except Exception as e:
        logging.error(f"Error while writing cleaned data: {e}")

# コマンドライン引数の設定
def attach_args(
    parser=argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    ),
):
    """
    コマンドライン引数を追加するヘルパー関数。

    戻り値:
    - 引数付きのArgumentParserオブジェクト
    """
    return ArgumentHelper(parser).add_distributed_args()

# スクリプトのエントリーポイント
if __name__ == "__main__":
    main(attach_args().parse_args())
