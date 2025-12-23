import streamlit as st
import os
from modules.image_analysis import analyze_image_content
from modules.story_generator import generate_story

# 設定頁面標題
st.set_page_config(page_title="AI Story Album", page_icon="📸")

def main():
    st.title("📸 AI Story Album")
    st.markdown("### Let Photos Tell Their Own Stories") # 對應報告 [cite: 3]

    # --- 側邊欄設定 (對應報告 [cite: 249]) ---
    st.sidebar.header("Configuration")
    
    # 風格選擇 - 對應報告 [cite: 153] 的風格個人化
    style = st.sidebar.selectbox(
        "Choose Story Style",
        ["Heartwarming (溫馨)", "Humorous (搞笑)", "Philosophical (文青/哲學)", "Cinematic (電影感)", "Horror (恐怖)"]
    )

    # --- 主要區域：上傳圖片 (對應報告 [cite: 238]) ---
    uploaded_file = st.file_uploader("Upload an image...", type=["jpg", "jpeg", "png"])

    if uploaded_file is not None:
        # 1. 顯示上傳的圖片
        st.image(uploaded_file, caption='Uploaded Image', use_column_width=True)
        
        # 建立按鈕開始生成
        if st.button('✨ Generate Story'):
            
            with st.spinner('Analyzing image features... (Vision AI)'):
                # [新增] 確保 temp 資料夾存在，如果不存在就自動建立
                if not os.path.exists("temp"):
                    os.makedirs("temp")
                # 為了讓 DeepFace 讀取，必須先將圖片存成暫存檔
                temp_path = os.path.join("temp", uploaded_file.name)
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # 呼叫 Image Analysis 模組
                # 對應報告 [cite: 242] 顯示摘要
                analysis = analyze_image_content(temp_path)
                caption = analysis.get("caption", "")
                emotion = analysis.get("emotion", "")
            
            # 顯示分析結果 (UI 視覺化)
            st.success("Analysis Complete!")
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"👀 **Scene:** {caption}")
            with col2:
                st.info(f"🎭 **Emotion:** {emotion}")
            if analysis.get("color_profile"):
                st.write(f"🎨 **Color Profile:** {analysis['color_profile']}")
            if analysis.get("tags"):
                st.write(f"🏷️ **Tags:** {', '.join(analysis['tags'])}")

            with st.spinner(f'Writing story in {style} style... (LLM)'):
                # 呼叫 Story Generator 模組
                story = generate_story(caption, emotion, style)

            # --- 最終輸出 (對應報告 [cite: 251]) ---
            st.markdown("---")
            st.markdown("### 📖 Your AI Story")
            st.write(story)
            
            # 清理暫存檔 (非必要，但保持整潔)
            os.remove(temp_path)

if __name__ == '__main__':
    main()
