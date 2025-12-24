# AI Story Album

**讓照片自己說故事**

AI Story Album 是一個將你的照片轉化為豐富敘事故事的專案。透過分析影像中的視覺內容與情緒線索，系統能自動生成一本故事書，將你的回憶轉換為獨一無二且個人化的體驗。

## Features

-   **情感敘事（Emotional Storytelling）：** AI 會根據場景、色彩與臉部表情生成具有情感深度的描述。
-   **風格客製化（Style Customization）：** 可選擇多種敘事風格，例如溫馨、幽默或詩意。
-   **全自動流程（Automated Process）：** 從影像分析、故事生成到 PDF 匯出，整個工作流程皆為自動化。
-   **前後端解耦架構（Decoupled Architecture）：** Vue.js 前端與 FastAPI 後端溝通，形成模組化且可擴展的系統。

## System Architecture

本應用由前端、後端，以及一組用於 AI 分析與生成的核心模組所組成。

-   **Frontend：** 使用 Vite 建置的 Vue.js 3 應用，提供使用者介面，用於上傳照片、選擇敘事風格，以及瀏覽生成的故事書。
-   **Backend：** 基於 Python 的 FastAPI 伺服器，提供 RESTful API 供前端呼叫，負責影像分析、故事生成與 PDF 匯出。
-   **Core Modules：**
    -   **Image Analyzer (`modules/image_analysis.py`)：** 此模組接收影像並使用 AI 模型（如 BLIP 與 DeepFace）擷取以下資訊：
        -   圖像描述文字（Caption）
        -   主要情緒
        -   色彩分佈特徵
        -   相關標籤
    -   **Story Generator (`modules/story_generator.py`)：** 此模組使用大型語言模型（LLM），例如 Gemini，根據分析結果與使用者選擇的風格生成完整故事。

## Getting Started

要執行 AI Story Album，你需要同時設定前端與後端環境。

### Prerequisites

-   Python 3.8 以上版本
-   Node.js 16 以上版本
-   Google Gemini（或其他相容 LLM）的 API Key

### Backend Setup

1.  **複製專案儲存庫：**
    ```bash
    git clone https://github.com/your-username/ai-story-album.git
    cd ai-story-album
    ```

2.  **建立虛擬環境並安裝相依套件：**
    ```bash
    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    ```

3.  **設定環境變數：**
    在專案根目錄建立 `.env` 檔案，並加入你的 API Key：
    ```
    GOOGLE_API_KEY="your_google_api_key"
    ```

4.  **啟動後端伺服器：**
    ```bash
    uvicorn main:app --reload
    ```
    後端伺服器將運行於 `http://localhost:8000`。

### Frontend Setup

1.  **進入前端目錄：**
    ```bash
    cd frontend
    ```

2.  **安裝相依套件：**
    ```bash
    npm install
    ```

3.  **啟動前端開發伺服器：**
    ```bash
    npm run dev
    ```
    前端應用將可於 `http://localhost:5173` 存取。

## API Endpoints

FastAPI 後端提供以下 API 端點：

-   `POST /api/analyze`：上傳一張或多張圖片進行分析。
-   `POST /api/story`：根據圖片分析結果生成故事書。
-   `POST /api/export`：將生成的故事書匯出為 PDF 檔案。
-   `GET /api/exports/{export_id}`：下載已匯出的 PDF。

## Project Structure

```
/
├── frontend/         # Vue.js frontend
├── modules/          # Core Python modules
│   ├── image_analysis.py
│   └── story_generator.py
├── temp/             # Temporary file storage
│   ├── uploads/
│   └── exports/
├── app.py            # Original Streamlit app (deprecated)
├── main.py           # FastAPI backend server
├── requirements.txt  # Python dependencies
└── ...
```

此 `README.md` 提供 AI Story Album 專案的完整概覽，包含系統架構以及如何快速啟動與執行的說明。
