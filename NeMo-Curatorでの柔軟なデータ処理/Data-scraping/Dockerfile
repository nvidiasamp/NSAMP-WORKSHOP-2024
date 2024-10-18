# NVIDIA NeMoのベースイメージを使用
FROM nvcr.io/nvidia/nemo:24.03.01.framework

# 作業ディレクトリを設定
WORKDIR /app

# プロジェクトファイルを作業ディレクトリにコピー
COPY . .

# requirements.txtファイルを作業ディレクトリにコピー
COPY requirements.txt .

# 必要なシステム依存関係をインストール
RUN apt-get update && apt-get install -y \
    build-essential \   
    cmake \   
    libopenblas-dev \   
    liblapack-dev \   
    libx11-dev \   
    libgtk-3-dev \   
    git \   
    wget \   
    unzip \   
    vim \   
    libcurl4-openssl-dev \   
    libssl-dev \   
    libffi-dev \   
    zlib1g-dev \   
    libjpeg-dev \   
    libpng-dev \   
    libtiff-dev \   
    poppler-utils \   
    libfreetype6-dev \
    && rm -rf /var/lib/apt/lists/*

# Python依存関係をインストール
RUN pip install --no-cache-dir -r requirements.txt

# PDF処理と描画用ライブラリをインストール
RUN pip install --no-cache-dir \
    PyMuPDF

# 環境変数を設定（必要に応じて）
ENV PYTHONUNBUFFERED=1

# アプリケーションの実行ポートを公開（仮に5000ポートとする）
EXPOSE 5000

# CMDは空のままにしておき、後で起動スクリプトを設定
CMD ["bash"]
