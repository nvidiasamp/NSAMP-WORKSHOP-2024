"""
このスクリプトは、指定されたURLリストからHTMLやPDFコンテンツを並列処理で効率的に取得し、テキストを抽出してJSONL形式で保存します。
リトライ機能付きのHTTPセッションを使い、ログ記録でエラーハンドリングや進捗状況を管理します。
"""

import os
import requests
from bs4 import BeautifulSoup
import json
import logging
import fitz  # PyMuPDF
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from logging.handlers import RotatingFileHandler
import argparse
import yaml
from tqdm import tqdm

def load_config(config_path):
    """
    設定ファイルを読み込む関数。
    
    パラメータ:
        config_path (str): 設定ファイルのパス。
    
    戻り値:
        dict: 設定ファイルの内容。
    """
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def setup_logging(log_folder, log_filename):
    """
    ログ記録の設定を行う。RotatingFileHandlerを使用してログファイルのサイズが大きくなりすぎないようにする。
    
    パラメータ:
        log_folder (str): ログファイルを保存するフォルダのパス。
        log_filename (str): ログファイルの名前。
    """
    ensure_directory_exists(log_folder)
    log_file_path = os.path.join(log_folder, log_filename)
    
    handler = RotatingFileHandler(log_file_path, maxBytes=10**6, backupCount=5)
    logging.basicConfig(level=logging.ERROR, handlers=[handler], format='%(asctime)s:%(levelname)s:%(message)s')

def create_session(headers):
    """
    HTTPリクエストのために、リトライ機能を備えたセッションを作成する。
    
    パラメータ:
        headers (dict): HTTPリクエストのヘッダー情報。
    
    戻り値:
        requests.Session: 設定済みのセッションオブジェクト。
    """
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
    session.mount('http://', HTTPAdapter(max_retries=retries))
    session.mount('https://', HTTPAdapter(max_retries=retries))
    session.headers.update(headers)
    return session

def scrape_website_with_session(session, url, timeout):
    """
    セッションを使用してウェブサイトをスクレイピングし、コンテンツタイプに応じてHTMLまたはPDFを処理する。
    
    パラメータ:
        session (requests.Session): セッションオブジェクト。
        url (str): スクレイピング対象のURL。
        timeout (int): リクエストのタイムアウト時間。
    
    戻り値:
        dict: タイトル、テキスト、URLを含む辞書。処理失敗時はNoneを返す。
    """
    try:
        response = session.get(url, timeout=timeout)
        response.raise_for_status()
        
        content_type = response.headers.get('Content-Type', '').lower()
        if 'application/pdf' in content_type:
            # PDFファイルを処理
            return {
                'title': os.path.basename(url),
                'text': extract_text_from_pdf(response.content),
                'url': url
            }
        elif 'text/html' in content_type:
            # HTMLファイルを処理
            soup = BeautifulSoup(response.text, 'html.parser')
            title = soup.find('title').text if soup.find('title') else 'No Title'
            paragraphs = [p.text for p in soup.find_all('p')]
            if not paragraphs:
                return None  # テキストがないページはスキップ
            text = ' '.join(paragraphs)
            return {'title': title, 'text': text, 'url': url}
        else:
            logging.warning(f"HTML/PDF以外のコンテンツタイプをスキップ: {content_type}，URL: {url}")
            return None
    except Exception as e:
        logging.error(f"スクレイピング中にエラーが発生しました {url}: {e}")
        return None

def extract_text_from_pdf(pdf_data):
    """
    PDFファイルからテキストを抽出する関数。
    
    パラメータ:
        pdf_data (bytes): PDFファイルのバイナリデータ。
    
    戻り値:
        str: 抽出されたテキスト内容。
    """
    try:
        pdf_text = ""
        with fitz.open("pdf", pdf_data) as pdf_document:
            for page_num in range(len(pdf_document)):
                page = pdf_document.load_page(page_num)
                pdf_text += page.get_text()
        return pdf_text
    except Exception as e:
        logging.error(f"PDFからテキストを抽出する際のエラー: {e}")
        return ""

def save_as_jsonl(data, filename):
    """
    データをJSONL形式でファイルに保存する関数（追記モード）。
    
    パラメータ:
        data (list): 保存するデータリスト。
        filename (str): 保存先のファイル名。
    """
    try:
        ensure_directory_exists(os.path.dirname(filename))
        with open(filename, 'a', encoding='utf-8') as f:
            for entry in data:
                if entry:
                    f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    except IOError as e:
        logging.error(f"データの保存中にエラーが発生しました {filename}: {e}")

def load_urls_from_file(file_path):
    """
    ファイルからURLリストを読み込む関数。
    
    パラメータ:
        file_path (str): URLリストを格納したファイルのパス。
    
    戻り値:
        list: 読み込まれたURLリスト。
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]
    except IOError as e:
        logging.error(f"URLリストをファイルから読み込む際にエラーが発生しました {file_path}: {e}")
        return []

def load_processed_urls(file_path):
    """
    処理済みのURLリストをファイルから読み込む関数。
    
    パラメータ:
        file_path (str): 処理済みURLリストを保存するファイルのパス。
    
    戻り値:
        set: 読み込まれた処理済みURLのセット。
    """
    if not os.path.exists(file_path):
        return set()
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return {line.strip() for line in f if line.strip()}
    except IOError as e:
        logging.error(f"処理済みURLの読み込み中にエラーが発生しました {file_path}: {e}")
        return set()

def append_to_processed_urls(file_path, url):
    """
    処理済みのURLをファイルに追加する関数。
    
    パラメータ:
        file_path (str): 処理済みURLを保存するファイルのパス。
        url (str): 追加する処理済みURL。
    """
    try:
        ensure_directory_exists(os.path.dirname(file_path))
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(url + '\n')
    except IOError as e:
        logging.error(f"処理済みURLの追加中にエラーが発生しました {file_path}: {e}")

def ensure_directory_exists(directory):
    """
    指定されたディレクトリが存在しない場合は作成する関数。
    
    パラメータ:
        directory (str): 作成するディレクトリのパス。
    """
    if not os.path.exists(directory):
        os.makedirs(directory)

def process_url(session, url, processed_urls_file, timeout):
    """
    URLを処理し、ウェブサイトの内容をスクレイピングし、処理済みURLを保存する。
    
    パラメータ:
        session (requests.Session): セッションオブジェクト。
        url (str): 処理対象のURL。
        processed_urls_file (str): 処理済みURLを保存するファイルのパス。
        timeout (int): リクエストのタイムアウト時間。
    
    戻り値:
        dict: スクレイピングしたデータ。処理失敗時はNoneを返す。
    """
    try:
        data = scrape_website_with_session(session, url, timeout)
        if data:
            append_to_processed_urls(processed_urls_file, url)
        return data
    except Exception as e:
        logging.error(f"URLの処理中にエラーが発生しました {url}: {e}")
        return None

def main(config):
    """
    メイン関数、URLのスクレイピングと処理タスクを実行する。
    
    パラメータ:
        config (dict): 設定ファイルの内容。
    """
    url_file = config['url_file']
    output_folder = config['output_folder']
    output_filename = os.path.join(output_folder, config['data_output_filename'])
    log_filename = config['log_filename']
    processed_urls_file = os.path.join(output_folder, config['processed_urls_filename'])
    
    setup_logging(output_folder, log_filename)
    ensure_directory_exists(output_folder)

    # URLの読み込み
    urls = load_urls_from_file(url_file)
    processed_urls = load_processed_urls(processed_urls_file)

    session = create_session(config['headers'])
    all_data = []
    failed_urls = []

    # 未処理のURLのみを処理対象とする
    urls_to_process = [url for url in urls if url not in processed_urls]

    # 並列処理でURLを処理
    with ThreadPoolExecutor(max_workers=config['max_workers']) as executor:
        future_to_url = {executor.submit(process_url, session, url, processed_urls_file, config['timeout']): url 
                         for url in urls_to_process}
        for future in tqdm(as_completed(future_to_url), total=len(urls_to_process), desc="Processing URLs"):
            url = future_to_url[future]
            try:
                data = future.result()
                if data:
                    all_data.append(data)
                else:
                    failed_urls.append(url)
            except Exception as exc:
                logging.error(f'{url} がエラーを生成しました: {exc}')
                print(f'{url} がエラーを生成しました: {exc}')
                failed_urls.append(url)

    # スクレイピングしたデータをJSONL形式で保存
    save_as_jsonl(all_data, output_filename)

    if failed_urls:
        print("\n以下のURLのスクレイピングに失敗しました:")
        for url in failed_urls:
            print(url)

    print(f"\nスクレイピングしたデータは {output_filename} に保存されました。")
    print(f"処理されたURLの合計数: {len(urls_to_process)}")
    print(f"成功したURL数: {len(all_data)}")
    print(f"失敗したURL数: {len(failed_urls)}")

if __name__ == "__main__":
    # コマンドライン引数の設定
    parser = argparse.ArgumentParser(description="URLデータのダウンロードと処理")
    parser.add_argument("--config", default='/app/config/config.yaml', help="設定ファイルのパス")
    args = parser.parse_args()

    # 設定ファイルを読み込んでメイン処理を実行
    config = load_config(args.config)
    main(config)
