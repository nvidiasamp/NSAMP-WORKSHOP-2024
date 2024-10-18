"""
このスクリプトは、指定された複数のURLからリンクを抽出し、特定のドメインを無視しながら結果をフィルタリングしてファイルに保存します。
並列処理を活用して効率的にURLを処理し、ログ機能でエラーや処理状況を記録します。また、すでに処理済みのURLはスキップする機能も含まれています。

主な機能:
- 複数のURLからリンクを抽出
- 無視するドメインのフィルタリング
- 処理済みURLのスキップと新規URLの処理
- ログの記録
- 結果のファイル保存
"""


import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
import os
import logging
from logging.handlers import RotatingFileHandler
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
from tqdm import tqdm
import yaml
import time

def load_config(config_path):
    """
    設定ファイルを読み込む。
    
    パラメータ:
        config_path (str): 設定ファイルのパス。
    
    戻り値:
        dict: 設定ファイルの内容。
    """
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def setup_logging(log_folder, log_filename):
    """
    ログ記録の設定を行う。
    
    パラメータ:
        log_folder (str): ログファイルを保存するフォルダ。
        log_filename (str): ログファイルの名前。
    """
    ensure_directory_exists(log_folder)
    log_file_path = os.path.join(log_folder, log_filename)
    handler = RotatingFileHandler(log_file_path, maxBytes=10**6, backupCount=5)
    logging.basicConfig(level=logging.ERROR, handlers=[handler], format='%(asctime)s:%(levelname)s:%(message)s')

def ensure_directory_exists(directory):
    """
    指定されたディレクトリが存在するか確認し、存在しない場合は作成する。
    
    パラメータ:
        directory (str): 作成するディレクトリのパス。
    """
    if not os.path.exists(directory):
        os.makedirs(directory)

def extract_links(url, headers, timeout):
    """
    指定されたURLからリンクを抽出する。
    
    パラメータ:
        url (str): 抽出対象のURL。
        headers (dict): HTTPリクエストヘッダ。
        timeout (int): リクエストのタイムアウト時間。
    
    戻り値:
        list: 抽出されたリンクのリスト。
    """
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()  # HTTPエラーが発生した場合に例外を投げる
        soup = BeautifulSoup(response.text, 'html.parser')
        # 正規表現を使用してリンクを抽出
        links = re.findall(r'href=["\'](.*?)["\']', str(soup))
        return [urljoin(url, link) for link in links]  # 相対リンクを絶対リンクに変換
    except requests.RequestException as e:
        logging.error(f"Request error for {url}: {e}")
        return []

def filter_links(links, ignored_domains):
    """
    特定のドメインを含むリンクを除外する。
    
    パラメータ:
        links (list): フィルタリング対象のリンクリスト。
        ignored_domains (list): 無視するドメインリスト。
    
    戻り値:
        list: フィルタリング後のリンクリスト。
    """
    return [link for link in links if not any(domain in link for domain in ignored_domains)]

def save_links_to_file(links, filepath):
    """
    リンクをファイルに保存する（追加モード）。
    
    パラメータ:
        links (list): 保存するリンクのリスト。
        filepath (str): 保存先ファイルのパス。
    """
    try:
        ensure_directory_exists(os.path.dirname(filepath))
        with open(filepath, 'a', encoding='utf-8') as file:
            for link in links:
                file.write(link + '\n')  # 各リンクをファイルに書き込む
    except IOError as e:
        logging.error(f"Error saving links to file {filepath}: {e}")

def read_urls_from_files(directory):
    """
    指定されたディレクトリ内の全てのtxtファイルからURLを読み取る。
    
    パラメータ:
        directory (str): URLが格納されたファイルのディレクトリ。
    
    戻り値:
        list: 読み取られたURLのリスト。
    """
    urls = []
    files_read = []
    try:
        for filename in os.listdir(directory):
            if filename.endswith('.txt'):  # txtファイルのみを対象とする
                files_read.append(filename)
                file_path = os.path.join(directory, filename)
                with open(file_path, 'r', encoding='utf-8') as file:
                    urls.extend([line.strip() for line in file if line.strip()])
    except IOError as e:
        logging.error(f"Error reading URLs from files in {directory}: {e}")
    return urls, files_read

def extract_links_with_retry(url, headers, timeout, max_retries=3):
    """
    URLからリンクを抽出する際に、指定された回数までリトライを試みる。
    
    パラメータ:
        url (str): 抽出対象のURL。
        headers (dict): HTTPリクエストヘッダ。
        timeout (int): リクエストのタイムアウト時間。
        max_retries (int): 最大リトライ回数。
    
    戻り値:
        list: 抽出されたリンクのリスト。
    """
    for attempt in range(max_retries):
        try:
            return extract_links(url, headers, timeout)
        except requests.RequestException as e:
            if attempt == max_retries - 1:
                logging.error(f"Failed to extract links from {url} after {max_retries} attempts: {e}")
                return []
            logging.warning(f"Attempt {attempt + 1} failed for {url}: {e}. Retrying...")
            time.sleep(2 ** attempt)  # エクスポネンシャルバックオフを使用して再試行

def process_url(url, headers, timeout, ignored_domains):
    """
    URLを処理し、リンクを抽出しフィルタリングする。
    
    パラメータ:
        url (str): 処理対象のURL。
        headers (dict): HTTPリクエストヘッダ。
        timeout (int): リクエストのタイムアウト時間。
        ignored_domains (list): 無視するドメインリスト。
    
    戻り値:
        list: フィルタリング後のリンクリスト。
    """
    links = extract_links_with_retry(url, headers, timeout)
    return filter_links(links, ignored_domains)

def load_processed_urls(file_path):
    """
    処理済みのURLリストをファイルから読み込む。
    
    パラメータ:
        file_path (str): 処理済みURLファイルのパス。
    
    戻り値:
        set: 処理済みURLのセット。
    """
    if not os.path.exists(file_path):
        return set()
    with open(file_path, 'r', encoding='utf-8') as f:
        return {line.strip() for line in f if line.strip()}

def append_to_processed_urls(file_path, url):
    """
    処理済みのURLをファイルに追加する。
    
    パラメータ:
        file_path (str): 処理済みURLファイルのパス。
        url (str): 追加するURL。
    """
    with open(file_path, 'a', encoding='utf-8') as f:
        f.write(url + '\n')

def main(config):
    """
    メイン関数、リンク抽出と処理タスクを実行する。
    
    パラメータ:
        config (dict): 設定ファイルの内容。
    """
    urls_directory = config['urls_directory']
    output_folder = config['output_folder']
    output_filepath = os.path.join(output_folder, config['output_filename'])
    log_filename = config['log_filename']
    processed_urls_file = os.path.join(output_folder, config['processed_urls_filename'])
    
    # ログ設定
    setup_logging(output_folder, log_filename)
    
    # URLをファイルから読み込み
    urls, files_read = read_urls_from_files(urls_directory)
    
    # 処理済みのURLをロード
    processed_urls = load_processed_urls(processed_urls_file)

    headers = config['headers']
    timeout = config['timeout']
    ignored_domains = config['ignored_domains']

    if not urls:
        print(f"No URLs to process in {urls_directory}")
        return

    print("読み込んだファイル：")
    for file in files_read:
        print(file)
    
    print(f"合計 {len(urls)} 件のURLを読み込みました。")

    all_links = set()
    urls_to_process = [url for url in urls if url not in processed_urls]

    # URLを並列処理
    with ThreadPoolExecutor(max_workers=config['max_workers']) as executor:
        future_to_url = {executor.submit(process_url, url, headers, timeout, ignored_domains): url for url in urls_to_process}
        for future in tqdm(as_completed(future_to_url), total=len(urls_to_process), desc="Processing URLs"):
            url = future_to_url[future]
            try:
                filtered_links = future.result()
                all_links.update(filtered_links)
                append_to_processed_urls(processed_urls_file, url)
            except Exception as exc:
                logging.error(f'{url} generated an exception: {exc}')
                print(f'{url} generated an exception: {exc}')

    # 抽出されたリンクをファイルに保存
    save_links_to_file(list(all_links), output_filepath)
    print(f"合計 {len(all_links)} 件のユニークリンクを抽出し、{output_filepath} に保存しました。")
    print(f"新しいURL {len(urls_to_process)} 件を処理しました。")

if __name__ == "__main__":
    # コマンドライン引数の設定
    parser = argparse.ArgumentParser(description="複数のURLからリンクを抽出するプログラム")
    parser.add_argument("--config", default='/app/config/config.yaml', help="設定ファイルのパス")
    args = parser.parse_args()

    # 設定ファイルを読み込んでメイン処理を実行
    config = load_config(args.config)
    main(config)
