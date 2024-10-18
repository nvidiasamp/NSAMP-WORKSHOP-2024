# Copyright (c) 2024, NVIDIA CORPORATION.  All rights reserved.
#
# このファイルはApache License 2.0のもとでライセンスされています。利用条件は上記URLで確認できます。
#
# このスクリプトは、ドキュメントデータセット内の重複データを検出し、重複を削除するためのものです。
# GPUまたはCPUでの実行に対応し、NeMo Curatorモジュールを使用しています。

import argparse
import time

from nemo_curator.datasets import DocumentDataset  # データセットの読み込みと処理
from nemo_curator.modules import ExactDuplicates  # 重複検出モジュール
from nemo_curator.utils.distributed_utils import get_client, read_data, write_to_disk  # データの読み込みと書き出し
from nemo_curator.utils.file_utils import get_all_files_paths_under  # ファイル検索ユーティリティ
from nemo_curator.utils.script_utils import ArgumentHelper  # スクリプト引数のヘルパー関数


def pre_imports():
    """
    GPUモードで実行する際に必要なライブラリを事前にインポートする関数。
    """
    import cudf  # GPU用のデータフレームライブラリ


def main(args):
    """
    メイン処理関数。データセットの読み込み、重複検出、重複データの削除を行います。

    パラメータ:
    - args: コマンドライン引数
    """

    # データセットとログ、出力ディレクトリのパス設定
    dataset_dir = "/workspace/data/mydata/split_curator/1_cleaned_pro"
    log_dir = "./"  # ログの保存ディレクトリ
    output_dir = "./"  # 出力データの保存ディレクトリ
    dataset_id_field = "title"  # 各データの識別フィールド（ここではタイトル）
    dataset_text_field = "text"  # 重複を検出する際に使用するテキストフィールド
    client = get_client(**ArgumentHelper.parse_client_args(args))  # クライアント設定
    backend = "cudf" if args.device == "gpu" else "pandas"  # 実行環境に応じてバックエンドを選択

    # GPUモードの場合、必要なインポートを実行
    if args.device == "gpu":
        client.run(pre_imports)

    # 処理開始時間の記録
    t0 = time.time()
    
    # データセットの読み込み（JSON形式）
    input_dataset = DocumentDataset.read_json(dataset_dir, backend=backend)

    # 重複検出モジュールのインスタンス化
    exact_dup = ExactDuplicates(
        logger=log_dir,
        id_field=dataset_id_field,
        text_field=dataset_text_field,
        # cache_dir=output_dir  # 必要に応じて出力をキャッシュに保存
    )

    # 重複データの検出
    duplicates = exact_dup(dataset=input_dataset)

    # キャッシュを使用する場合、結果はキャッシュに保存されたデータセットへのパス
    if isinstance(duplicates, str):
        duplicates = DocumentDataset.read_parquet(duplicates, backend=backend)

    # データフレーム操作を簡単にするため、df（データフレーム）を利用可能

    # 重複IDをすべて取得し、最初の1つを残して他の重複を削除する設定
    docs_to_remove = duplicates.df.map_partitions(
        lambda x: x[x._hashes.duplicated(keep="first")]
    )

    # 重複が少ない場合、計算結果をリストに格納し、`isin`を使ってデータをフィルタリング
    result = input_dataset.df[
        ~input_dataset.df[dataset_id_field].isin(
            docs_to_remove[dataset_id_field].compute()
        )
    ]

    # 重複のないデータセットをディスクに保存（Parquet形式）
    write_to_disk(result, output_dir, output_type="parquet")

    # 処理にかかった時間を表示
    print(time.time() - t0)


# コマンドライン引数の設定
def attach_args(
    parser=argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    ),
):
    """
    コマンドライン引数を定義する関数。

    戻り値:
    - 引数を追加したArgumentParserオブジェクト
    """
    return ArgumentHelper(parser).add_distributed_args()


# スクリプトのエントリーポイント
if __name__ == "__main__":
    main(attach_args().parse_args())
