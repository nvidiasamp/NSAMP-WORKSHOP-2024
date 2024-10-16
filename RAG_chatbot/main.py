############################################
# Component #1 - Document Loader
# ユーザーがアプリの中でファイルをアップロードするための仕組み
############################################


import streamlit as st
import os

# ページのレイアウトを設定（幅広レイアウト）
st.set_page_config(layout="wide")

with st.sidebar:
    # ドキュメントを保存するディレクトリのパスを設定
    DOCS_DIR = os.path.abspath("./uploaded_docs")
    # ディレクトリが存在しない場合は作成
    if not os.path.exists(DOCS_DIR):
        os.makedirs(DOCS_DIR)
    # サイドバーにサブヘッダーを表示
    st.subheader("Knowledge Baseに追加")
    # フォームを作成（送信後にクリア）
    with st.form("my-form", clear_on_submit=True):
        # ファイルアップローダーを設置（複数ファイルを許可）
        uploaded_files = st.file_uploader(
            "Knowledge Baseへのファイルのアップロード:", accept_multiple_files=True
        )
        # アップロードボタン
        submitted = st.form_submit_button("アップロード")

    # ファイルがアップロードされ、ボタンが押された場合
    if uploaded_files and submitted:
        for uploaded_file in uploaded_files:
            # アップロード成功のメッセージを表示
            st.success(f"File {uploaded_file.name} のアップロードが完了しました")
            # ファイルを指定のディレクトリに保存
            with open(os.path.join(DOCS_DIR, uploaded_file.name), "wb") as f:
                f.write(uploaded_file.read())

############################################
# Component #2 - Embedding Model and LLM
# NVIDIAが提供するAIモデルの設定
############################################

from langchain_nvidia_ai_endpoints import ChatNVIDIA, NVIDIAEmbeddings

# NVIDIA AI PlaygroundのAPIキーを環境変数に設定しておく必要があります（NVIDIA_API_KEY）
# LLMモデルを初期化
llm = ChatNVIDIA(model="ai-llama3-70b")
# ドキュメント用の埋め込みモデルを初期化
document_embedder = NVIDIAEmbeddings(model="ai-embed-qa-4", model_type="passage")
# クエリ用の埋め込みモデルを初期化
query_embedder = NVIDIAEmbeddings(model="ai-embed-qa-4", model_type="query")

############################################
# Component #3 - Vector Database Store
# ベクトルストアの設定
############################################

from langchain.text_splitter import CharacterTextSplitter
from langchain_community.document_loaders import DirectoryLoader
from langchain_community.vectorstores import FAISS
import pickle

with st.sidebar:
    # 既存のベクトルストアを使用するかの選択肢を提供
    use_existing_vector_store = st.radio(
        "既存のベクトルストアーを使用しますか？", ["Yes", "No"], horizontal=True
    )

# ベクトルストアの保存先ファイルパス
vector_store_path = "vectorstore.pkl"

# ドキュメントディレクトリから生のドキュメントをロード
raw_documents = DirectoryLoader(DOCS_DIR).load()

# 既存のベクトルストアファイルが存在するか確認
vector_store_exists = os.path.exists(vector_store_path)
vectorstore = None
if use_existing_vector_store == "Yes" and vector_store_exists:
    # 既存のベクトルストアをロード
    with open(vector_store_path, "rb") as f:
        vectorstore = pickle.load(f)
    with st.sidebar:
        st.success("既存のベクトルストアのロードが完了しました")
else:
    with st.sidebar:
        if raw_documents:
            # ドキュメントをチャンクに分割
            with st.spinner("Splitting documents into chunks..."):
                text_splitter = CharacterTextSplitter(
                    chunk_size=500, chunk_overlap=100
                )
                documents = text_splitter.split_documents(raw_documents)

            # チャンクをベクトルストアに追加
            with st.spinner("Adding document chunks to vector database..."):
                vectorstore = FAISS.from_documents(documents, document_embedder)

            # ベクトルストアをファイルに保存
            with st.spinner("Saving vector store"):
                with open(vector_store_path, "wb") as f:
                    pickle.dump(vectorstore, f)
            st.success("Vector store created and saved.")
        else:
            # ドキュメントがない場合の警告
            st.warning("No documents available to process!", icon="⚠️")

############################################
# Component #4 - LLM Response Generation and Chat
# 応答の生成と対話
############################################

# メインのチャットセクションのヘッダーを表示
st.subheader("LLMとの会話が可能です")

# セッション状態にメッセージがなければ初期化
if "messages" not in st.session_state:
    st.session_state.messages = []

# これまでのメッセージを表示
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

# プロンプトテンプレートを定義
prompt_template = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "あなたは役に立つAIアシスタントです。ユーザの入力には必ず日本語で返答してください。",
        ),
        ("user", "{input}"),
    ]
)
# ユーザーの入力を受け取る（チャット入力）
user_input = st.chat_input("Can you tell me what NVIDIA is known for?")
# LLMモデルを再度初期化（必要に応じて）
llm = ChatNVIDIA(model="ai-llama3-70b")

# プロンプトテンプレートとLLMをチェーンし、文字列出力パーサーを適用
chain = prompt_template | llm | StrOutputParser()

# ユーザーの入力がある場合
if user_input:
    # セッション状態にユーザーのメッセージを追加
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.chat_message("user").markdown(user_input)

    if vectorstore is not None:
        # ベクトルストアのレトリーバーを取得（上位2つの関連ドキュメントを取得）
        retriever = vectorstore.as_retriever(search_kwargs={"k": 2})
        # ユーザーの入力に基づいてドキュメントを検索
        docs = retriever.invoke(user_input)

        # 取得したドキュメントからコンテキストを生成
        context = ""
        for doc in docs:
            context += doc.page_content + "\n\n"

        # コンテキストとユーザーの質問を組み合わせて入力を強化
        augmented_user_input = f"Context: {context}\n\nQuestion: {user_input}\n"
    else:
        # ベクトルストアがない場合、コンテキストなしで応答
        augmented_user_input = f"Question: {user_input}\n"

    with st.chat_message("assistant"):
        # メッセージのプレースホルダーを作成
        message_placeholder = st.empty()
        full_response = ""

        # LLMからの応答をストリーミングで取得
        for response in chain.stream({"input": augmented_user_input}):
            full_response += response
            # 応答を逐次的に表示（カーソルを表示）
            message_placeholder.markdown(full_response + "▌")
        # 最終的な応答を表示
        message_placeholder.markdown(full_response)

    # セッション状態にアシスタントのメッセージを追加
    st.session_state.messages.append({"role": "assistant", "content": full_response})
