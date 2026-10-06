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

if st.button("ダウンロード準備"):
    if not url:
        st.warning("URLを入力してください。")
    else:
        with st.spinner("今使えるプロキシ（身代わりIP）を探索中..."):
            # 無料のプロキシリストから、有効そうなHTTPプロキシを自動取得する
            proxy_url = None
            try:
                # ProxyScrapeなどの公開APIからプロキシ一覧を取得
                res = requests.get("https://proxyscrape.com")
                if res.status_code == 200 and res.text:
                    proxies = [p.strip() for p in res.text.split("\n") if p.strip()]
                    if proxies:
                        # 取得したリストからランダムに1つ選ぶ
                        selected_proxy = random.choice(proxies)
                        proxy_url = f"http://{selected_proxy}"
                        st.info(f"💡 プロキシを使用します: {selected_proxy}")
            except Exception as proxy_err:
                st.warning("無料プロキシの自動取得に失敗しました。サーバーIPで直接試行します。")

        with st.spinner("動画情報を取得中..."):
            try:
                download_dir = "downloads"
                if not os.path.exists(download_dir):
                    os.makedirs(download_dir)
                
                for f in glob.glob(f"{download_dir}/*"):
                    try: os.remove(f)
                    except: pass

                # 共通オプション
                common_opts = {
                    'extractor_args': {'youtube': {'client': ['ios', 'android']}},
                    'sleep_requests': 2,
                    'source_address': '0.0.0.0',
                    'ignoreerrors': True,
                }

                # プロキシが見つかっていれば設定に追加する
                if proxy_url:
                    common_opts['proxy'] = proxy_url

                # （以下、以前の ydl_opts の処理へ続く...）

                if option == "動画 (最良画質 MP4)":
                    ydl_opts = {
                        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
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
                    info = ydl.extract_info(url, download=True)
                    filename = ydl.prepare_filename(info)
                    
                    if option == "音声のみ (MP3)":
                        filename = os.path.splitext(filename)[0] + ".mp3"

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
                    st.error("ファイルの生成に失敗しました。")

            except Exception as e:
                st.error(f"エラーが発生しました: {str(e)}")
                st.info("Renderなどの無料サーバーでは、YouTubeのIP制限やFFmpegの未インストールによりエラーが出る場合があります。")

