import streamlit as st
import yt_dlp
import os
import glob

st.set_page_config(page_title="YouTube Downloader", page_icon="🎥", layout="centered")

st.title("🎥 YouTube 動画ダウンローダー")
st.write("URLを入力して、動画または音声（MP3）をダウンロードできます。")

# URL入力
url = st.text_input("YouTubeの動画URLを入力してください:", placeholder="https://www.youtube.com/watch?v=...")

# ダウンロードオプション
option = st.radio("ダウンロード形式を選択してください:", ("動画 (最良画質 MP4)", "音声のみ (MP3)"))

if st.button("ダウンロード準備"):
    if not url:
        st.warning("URLを入力してください。")
    else:
        with st.spinner("動画情報を取得中..."):
            try:
                # 一時保存用のディレクトリ
                download_dir = "downloads"
                if not os.path.exists(download_dir):
                    os.makedirs(download_dir)
                
                # クリーンアップ（古いファイルを消去）
                for f in glob.glob(f"{download_dir}/*"):
                    try:
                        os.remove(f)
                    except:
                        pass

                # yt-dlpのオプション設定
                if option == "動画 (最良画質 MP4)":
                    ydl_opts = {
                        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                        'outtmpl': f'{download_dir}/%(title)s.%(ext)s',
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
                    }

                # ダウンロード実行
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    filename = ydl.prepare_filename(info)
                    
                    if option == "音声のみ (MP3)":
                        filename = os.path.splitext(filename)[0] + ".mp3"

                # 正常に作成されたか確認
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
