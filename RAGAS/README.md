# Requirement
### 実行環境
python 3.9.13

### ライブラリ
requirements.txtを参照


# Installation
### docker
1. ローカルの作業フォルダに移動
2. `git clone https://github.com/nvidiasamp/Evaluate_RAG.git`
3. `cd evaluate_rag`
4. `docker build -t my-python-app .`
5. `docker run -it my-python-app .`

# venv
1. `git clone https://github.com/nvidiasamp/Evaluate_RAG.git`
2. `cd evaluate_rag`
3. `python -m venv venv`
4. `venv\Scripts\activate`
5. `pip install -r requirements.txt`