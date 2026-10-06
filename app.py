import streamlit as st
import yt_dlp
import os
import glob
import requests
import random

st.set_page_config(page_title="YouTube Downloader", page_icon="🎥", layout="centered")

st.title("🎥 YouTube 動画ダウンローダー")
st.write("URLを入力して、動画または音声（MP3）をダウンロードできます。")

url = st.text_input("YouTubeの動画URLを入力してください:", placeholder="https://youtube.com...")
option = st.radio("ダウンロード形式を選択してください:", ("動画 (最良画質 MP4)", "音声のみ (MP3)"))

# --- 安全なプロキシを取得・検証する関数 ---
def get_verified_proxy():
    # 複数の無料プロキシAPI候補
    urls = [
        "https://proxyscrape.com",
        "https://pubproxy.com"
    ]
    
    for api_url in urls:
        try:
            res = requests.get(api_url, timeout=4)
            if res.status_code == 200 and res.text:
                # 行ごとに分割してクリーンアップ
                proxies = [p.strip() for p in res.text.split("\n") if p.strip() and not p.startswith("<")]
                if not proxies:
                    continue
                
                # ランダムに3つ抽出してテスト
                random.shuffle(proxies)
                for test_proxy in proxies[:3]:
                    proxy_url = f"http://{test_proxy}"
                    try:
                        # 実際にGoogleへの接続テストを行い、応答があるか確認
                        test_res = requests.get("https://google.com", proxies={"http": proxy_url, "https": proxy_url}, timeout=2)
                        if test_res.status_code == 200:
                            return proxy_url # 生きているプロキシを返す
                    except:
                        continue # 死んでいるプロキシはスキップ
        except:
            continue
    return None

if st.button("ダウンロード準備"):
    if not url:
        st.warning("URLを入力してください。")
    else:
        proxy_url = None
        with st.spinner("生存しているプロキシ（身代わりIP）を探索・検証中..."):
            proxy_url = get_verified_proxy()
            if proxy_url:
                st.info(f"💡 検証済みのプロキシを使用します: {proxy_url}")
            else:
                st.warning("有効な無料プロキシが見つかりませんでした。サーバーの直接IPで通信を試みます。")

        with st.spinner("動画情報を取得・ダウンロード中...（1〜2分かかる場合があります）"):
            try:
                download_dir = "downloads"
                if not os.path.exists(download_dir):
                    os.makedirs(download_dir)
                
                # 過去のキャッシュファイルを削除
                for f in glob.glob(f"{download_dir}/*"):
                    try: os.remove(f)
                    except: pass

                # 共通オプション設定
                # 共通オプション設定
                common_opts = {
                    'extractor_args': {'youtube': {'client': ['ios', 'android']}},
                    'sleep_requests': 2,
                    'source_address': '0.0.0.0',
                    'ignoreerrors': False,
                    'quiet': False,
                    # ─── 【追加】普段使っているブラウザを指定（例: 'chrome', 'edge', 'firefox', 'safari'） ───
                    'cookiesfrombrowser': ('safari',), 
                }


                # 生存確認が取れたプロキシのみ yt-dlp に渡す（setdefaultエラー対策の核心）
                if proxy_url:
                    common_opts['proxy'] = proxy_url

                if option == "動画 (最良画質 MP4)":
                    ydl_opts = {
                        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/mp4/best',
                        'outtmpl': f'{download_dir}/%(title)s.%(ext)s',
                        **common_opts
                    }
                else:
                    ydl_opts = {
                        'format': 'bestaudio/best',
                        'outtmpl': f'{download_dir}/%(title)s.%(ext)s',
                        'postprocessors': [{
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': 'mp3',
                            'preferredquality': '192',
                        }],
                        **common_opts
                    }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    # ダウンロードを実行
                    info = ydl.extract_info(url, download=True)
                    
                    # 万が一NoneTypeが返ってきた場合の防御ガード
                    if info is None:
                        raise Exception("YouTubeから動画データを取得できませんでした。IPが制限されている可能性があります。")
                    
                    # プレイリストか単一動画かを判定
                    info_data = info['entries'][0] if 'entries' in info else info
                    
                    # 予測ファイル名を取得
                    filename = ydl.prepare_filename(info_data)
                    
                    # 音声変換（MP3）の拡張子補正
                    if option == "音声のみ (MP3)":
                        filename = os.path.splitext(filename)[0] + ".mp3"
                    
                    # 万が一 yt-dlp が想定外の拡張子（.webmや.mkv）で保存した場合の救済措置
                    if not os.path.exists(filename):
                        base_path = os.path.splitext(filename)[0]
                        found_files = glob.glob(f"{base_path}.*")
                        if found_files:
                            filename = found_files[0]

                # 最終ファイル確認とダウンロードボタンの生成
                if os.path.exists(filename):
                    with open(filename, "rb") as f:
                        file_data = f.read()
                    
                    st.success("準備が完了しました！以下のボタンから保存してください。")
                    st.download_button(
                        label="ファイルをダウンロード",
                        data=file_data,
                        file_name=os.path.basename(filename),
                        mime="video/mp4" if option == "動画 (最良画質 MP4)" else "audio/mpeg"
                    )
                else:
                    st.error("エラー: ファイルのダウンロードまでは成功しましたが、保存先パスが一致しませんでした。")

            except Exception as e:
                # ユーザーフレンドリーなエラーハンドリング
                error_msg = str(e)
                st.error(f"ダウンロードに失敗しました。")
                with st.expander("詳細なエラーログを確認"):
                    st.code(error_msg)
                
                st.info("💡 **対策のヒント:**\n"
                        "1. **もう一度実行ボタンを押す**: 無料プロキシが途中で切れた可能性があるため、再試行で別のプロキシを引くと成功することがあります。\n"
                        "2. **ローカルPC環境で試す**: クラウドサーバー（Render等）のIPはYouTubeに嫌われているため、ご自身のPCのVSCodeなどで動かすと一発で成功しやすいです。\n"
                        "3. **ライブラリの更新**: ターミナルで `pip install -U yt-dlp` を実行して、最新のYouTube仕様に対応させてください。")
