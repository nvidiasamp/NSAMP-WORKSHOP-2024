# Copyright (c) 2024, NVIDIA CORPORATION.  All rights reserved.
#
# このファイルはApache License 2.0のもとでライセンスされています。
# このスクリプトは、指定されたデータセットからタスクに関連するデータを除外（decontaminate）し、
# クリーンなデータセットを出力するために使用されます。

import argparse

import nemo_curator as nc  # NeMo Curator モジュール
from nemo_curator.datasets import DocumentDataset  # ドキュメントデータセット
from nemo_curator.tasks import (  # タスク群（除外対象として使うデータセット）
    ANLI,
    CB,
    PIQA,
    RTE,
    WSC,
    ArcChallenge,
    ArcEasy,
    BoolQ,
    Copa,
    Drop,
    MultiRC,
    OpenBookQA,
    Quac,
    Race,
    Record,
    Squad,
    TriviaQA,
    WebQA,
    WiC,
    Winogrande,
)
from nemo_curator.utils.distributed_utils import get_client, read_data, write_to_disk  # データ操作ユーティリティ
from nemo_curator.utils.file_utils import get_all_files_paths_under  # ファイル操作ユーティリティ
from nemo_curator.utils.script_utils import ArgumentHelper  # スクリプト引数ヘルパー


# データセットを読み込む関数
def load_dataset(input_data_dir):
    """
    指定されたディレクトリからファイルを読み込み、データセットとして返します。

    パラメータ:
    - input_data_dir: データのディレクトリパス

    戻り値:
    - 読み込まれたドキュメントデータセット
    """
    files = list(get_all_files_paths_under(input_data_dir))  # ディレクトリ内のすべてのファイルを取得
    raw_data = read_data(files, file_type="jsonl", backend="pandas", add_filename=True)  # JSONLファイルを読み込み
    dataset = DocumentDataset(raw_data)  # データセットを作成

    return dataset


# メイン処理
def main(args):
    """
    データセットを読み込み、タスクに関連するデータを除外し、クリーンなデータセットを出力します。

    パラメータ:
    - args: コマンドライン引数
    """
    # データセットのパス設定
    contaminated_dataset_path = "/workspace/data/mydata/split_curator/1_cleaned_pro"  # 除去前のデータセット
    decontaminated_output_path = "/workspace/data/mydata/split_curator/3_decontamination_pro"  # 除去後の出力先

    # 除去の対象となるダウンストリームタスクを定義
    downstream_tasks = [
        Winogrande(),
        Squad(),
        TriviaQA(),
        Quac(),
        WebQA(),
        Race(),
        Drop(),
        WiC(),
        PIQA(),
        ArcEasy(),
        ArcChallenge(),
        OpenBookQA(),
        BoolQ(),
        Copa(),
        RTE(),
        MultiRC(),
        WSC(),
        CB(),
        ANLI(),
        Record(),
    ]

    # クライアント設定の準備
    client = get_client(**ArgumentHelper.parse_client_args(args))

    # データセットの読み込み
    target_dataset = load_dataset(contaminated_dataset_path)

    # 除去処理のインスタンス化と適用
    decontaminator = nc.TaskDecontamination(downstream_tasks)
    decontaminated_dataset = decontaminator(target_dataset)

    # フィルタリングされたデータセットをディスクに書き出し
    write_to_disk(
        decontaminated_dataset.df, decontaminated_output_path, write_to_filename=True
    )


# コマンドライン引数の設定
def attach_args(
    parser=argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    ),
):
    """
    コマンドライン引数を追加するヘルパー関数。

    戻り値:
    - 引数を追加したArgumentParserオブジェクト
    """
    return ArgumentHelper(parser).add_distributed_args()


# スクリプトのエントリーポイント
if __name__ == "__main__":
    main(attach_args().parse_args())
