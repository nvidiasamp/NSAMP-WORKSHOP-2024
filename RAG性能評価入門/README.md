# RAG性能評価入門

## 概要

RAGで生成した回答に対して、NVIDIAが提供するモデル(nemotron-4-340b-reward)を用いて性能評価を行う
src/evaluate_rag.ipynbを実行することでJaQuADを用いた性能評価のデモが可能

## 実行環境

python 3.9.13
CPU:AMD Ryzen 9 5900X 12-Core Processor
RAM:48GB

## ライブラリ

requirements.txtを参照

## 仮想環境の準備

dockerまたはvenvを使用して仮想環境を構築する

### docker

1. ローカルの作業フォルダに移動
2. `git clone https://github.com/nvidiasamp/RAG性能評価入門.git`
3. `cd RAG性能評価入門`
4. `docker build -t my-python-app .`
5. `docker run -it my-python-app .`

### venv

1. `git clone https://github.com/nvidiasamp/RAG性能評価入門.git`
2. `cd RAG性能評価入門`
3. `python -m venv venv`
4. `venv\Scripts\activate`
5. `pip install -r requirements.txt`
