# MONAIによる3Dセグメンテーション入門
## 概要
MONAIによる3Dセグメンテーションの基本的な流れを紹介します。

## 環境
以下のイメージを使用してください。
- [MONAI Toolkit](https://catalog.ngc.nvidia.com/orgs/nvidia/teams/clara/containers/monai-toolkit)
  - nvcr.io/nvidia/clara/monai-toolkit:1.1-2

### ハードウェアの要件(使用したハードウェア)
- CUDA: 11.0
- NVIDIA driver: 450.236.01

###  GPU要件（使用したGPU）
- Tesla V100 32GB × 2

## 使用したデータ
- 公式ホームページ：[KiTS19 Grand Challenge](https://kits19.grand-challenge.org/)
- [GitHubリポジトリ](https://github.com/neheller/kits19)

以下のようにダウンロードしてください。
```
git clone https://github.com/neheller/kits19
cd kits19
python3 -m starter_code.get_imaging
```

## 事前学習モデルのダウンロード
```
wget -O /output_dir/output_filepath https://github.com/Project-MONAI/MONAI-extra-test-data/releases/download/0.8.1/model_swinvit.pt
```

## 参考文献
- [MONAI Tutorials](https://github.com/Project-MONAI/tutorials)
