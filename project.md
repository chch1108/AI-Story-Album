# AI Story Album — 系統開發規格書 (Project Specification)

Let Photos Tell Their Own Stories

## 1. 專案概述 (Project Overview)

AI Story Album 的目標是讓相片擁有情境與情感敘事，而非僅停留在標籤與分類。透過 AI 模組化流程，將 From pixels to prose 的願景轉化為具體產品體驗。

### 1.1 背景與痛點
- 現有相簿系統（Google Photos、Apple Memories）著重管理、搜尋功能，缺乏敘事層的語境生成。
- 使用者需要將照片整理成故事或文字內容時，仍需手動撰寫；影像內容的情緒價值難以被放大。

### 1.2 產品目標
- 將照片從靜態記錄轉為富含情緒、語氣與風格的故事文本。
- 讓使用者能快速生成具有個人風格的故事書並分享。
- 支援從手機、網頁或 IoT 裝置資料流入，打造跨場域體驗。

### 1.3 核心價值主張
- **情感敘事 (Emotional Storytelling)**：AI 根據場景、顏色與人物表情自動生成具情緒張力的描述。
- **風格客製化 (Style Customization)**：使用者可自由切換敘事語氣，例如溫馨、搞笑、文青或旅遊紀錄。
- **全流程自動化**：從影像分析、故事生成到故事書排版輸出皆由系統協作完成。

### 1.4 成功指標 (KPIs)
- 生成故事滿意度（問卷），目標 ≥ 85%。
- 單張照片故事生成延遲 < 2 秒；批次處理 10 張照片需 < 20 秒。
- 使用者回訪率（30 天內）≥ 40%。

## 2. 系統架構與工作流 (System Architecture & Pipeline)

整體系統採模組化設計，從前端輸入到故事輸出分為以下四層：

```
Input Layer → Analysis Layer → Generation Layer → Presentation Layer
```

| Layer | 責任 | 主要輸入/輸出 |
| --- | --- | --- |
| Input Layer | 圖片與 metadata 收集 | 使用者照片、IoT 端影像 → 二進位資料、EXIF |
| Analysis Layer | 影像轉語意/情緒特徵 | 圖像 → JSON 特徵描述 |
| Generation Layer | 文字故事生成 | JSON 特徵 + Style Token → 故事文本 |
| Presentation Layer | 故事書排版、輸出管道 | 故事文本 + 圖片 → PDF/Web/eBook |

資料流由 API Gateway 負責調度，各模組可獨立部署並透過 message queue 或 REST 交互。

### 2.1 應用分層（前後端分離、全本地開發）

- **前端 (Vue 3 + Vite)**：負責圖片上傳、分析結果可視化、風格選擇與故事預覽。使用 Pinia 管理狀態（上傳檔案、分析 JSON、生成故事），透過 Axios 呼叫本地 API（`http://localhost:8000/api/*`）。開發時以 `npm run dev` 在 `localhost:5173` 執行，並提供 mock data 模式以脫機測試。
- **後端 (FastAPI / Python)**：封裝現有模組 `modules.image_analysis` 與 `modules.story_generator`，新增 RESTful 介面：`POST /api/analyze`、`POST /api/story`、`POST /api/export`。使用 Uvicorn 本地啟動 (`localhost:8000`)，負責檔案暫存、模型推論、故事生成、排版任務排程。
- **資料交換格式**：前端以 `multipart/form-data` 上傳圖片，後端回傳規格化 JSON（見 3.1/3.2 Output Schema）。後端對 Vue 提供 SSE / WebSocket 更新，支援長任務狀態。
- **本地執行流程**：`npm install` 後啟動 Vue，再以 `poetry run uvicorn main:app --reload` 或 `python -m uvicorn` 啟動 API。兩者透過 CORS 允許本地跨來源。

## 3. 詳細技術規格 (Technical Specifications)

### 3.1 模組一：圖像分析器 (Image Analyzer)

**功能**：將非結構化圖像轉換為包含語意、情緒與色彩特徵的 JSON 資料，供後續 LLM 生成故事使用。

**輸入格式**：`.jpg`, `.png`，支援附帶 Metadata（GPS、Timestamp、Device）。

**技術堆疊**
- 場景描述 (Captioning)：BLIP、CLIP、Vision Transformer (VILA)
- 情緒偵測 (Emotion Detection)：DeepFace、FER2013 finetuned models
- 顏色特徵：OpenCV Histogram（亮度、飽和度、主色調）

**Pseudo-code**
```python
def analyze_image(image):
    caption = BLIP.generate_caption(image)
    emotion = DeepFace.analyze(image)["dominant_emotion"]
    color_hist = extract_color_histogram(image)
    tags = CLIP.tag_objects(image)

    return {
        "caption": caption,
        "emotion": emotion,
        "color_profile": color_hist,
        "tags": tags
    }
```

**Output JSON Schema**
```json
{
  "caption": "two kids playing on the beach",
  "emotion": "happy",
  "color_profile": {
    "brightness": 0.72,
    "saturation": 0.64,
    "dominant_colors": ["sand", "sky"]
  },
  "tags": ["beach", "kids", "outdoor"],
  "metadata": {
    "timestamp": "2024-04-11T10:32:00Z",
    "gps": [121.560, 25.033]
  }
}
```

### 3.2 模組二：故事生成引擎 (Story Engine / LLM Integration)

**功能**：根據 Image Analyzer JSON 與使用者指定的風格參數產生具敘事張力的故事。支援多語輸出與可調語氣。

**輸入**
- Image Analyzer 的 JSON
- Style Parameters（語言、語氣、篇幅、觀點）

**核心模型**
- GPT、Gemini、Claude（可依場景切換）
- 可選用自訓練 LoRA 以降低成本

**Prompt Strategy**
```
Role: You are a storyteller.
Context: Use the scene, emotion, and visual tone from the JSON.
Style: {Selected Style Token}
Constraints: Keep description truthful to the photo.
Language: {user_locale}
```

**Supported Style Tokens**
| Style | 說明 |
| --- | --- |
| Heartwarming (溫馨) | 強調陪伴、溫度、回憶 |
| Humorous (搞笑) | 誇張語氣、意外反差 |
| Poetic / Introspective (文青/詩意) | 光影、哲思、內心旁白 |
| Travelogue (旅遊) | 地點與行程描寫 |
| Romantic (浪漫) | 柔和語氣、夢幻意象 |
| Minimal Documentary | 簡潔事實敘述，適合相簿標註 |

**LLM 參數建議**
- `temperature`: 0.7（可依風格調整）
- `max_tokens`: 200–400
- `top_p`: 0.9
- few-shot examples：確保敘事風格一致
- Response schema：`{"title": str, "body": str, "quotes": [str]}`

### 3.3 模組三：使用者介面 (User Interface & Interaction)

**使用者流程**
1. 上傳圖片（支援拖拉與批次）
2. 顯示 AI 分析摘要（caption、emotion、色彩 tag）
3. 選擇敘事風格與語言
4. 按下 `Generate Story`，呈現故事預覽與排版樣式
5. 可手動微調故事內容或重新生成
6. 儲存/分享故事書（PDF、Web link）

**介面要求**
- 版本控制：保存故事歷史版本與使用者編輯記錄
- 即時預覽：使用 Composer API 預覽排版效果
- 可存取 token 用量與估計成本，提示使用者

### 3.4 模組四：排版合成器 (Storybook Composer)

**輸入**：LLM 生成故事、原始圖片、UI 設定（版面、字型、主題色）。

**技術工具**
- PDF：ReportLab、WeasyPrint
- Web：HTML/CSS Renderer + Tailwind/Chakra
- 動態書籍：Turn.js、Canvas-based Animation

**輸出格式**
- PDF Storybook（適合列印或分享）
- Web Interactive Storybook（翻頁動畫、音樂）
- ePub / eBook

### 3.5 可選模組：IoT 整合

**硬體**：Raspberry Pi + Camera Module，附 GPS, LTE/WiFi。

**功能**
- 定時拍照、自動上傳伺服器
- Edge 端執行輕量模型（MobileNet 或 CLIP mini）進行基本分類
- 當無網路時進行緩存，恢復連線後批次上傳

## 4. 系統整合與 API

### 4.1 API Gateway 設計
- `/upload`：接收圖片，返回圖像 ID。
- `/analyze/{image_id}`：呼叫 Image Analyzer，產出 JSON。
- `/story`：提供 JSON + style token，返回故事文本。
- `/compose`：生成 PDF/Web/eBook，返回下載連結。

所有 API 採 JWT 驗證，支援使用者層級配額控制。

### 4.2 Message Queue (可選)
- 使用 RabbitMQ / Kafka 作為事件總線，保證批次處理可靠性。
- 事件：`image.uploaded`, `analysis.completed`, `story.generated`, `book.rendered`。

## 5. 測試與驗證計畫 (Testing & Evaluation)

1. **單元測試 (Unit Tests)**
   - Image Analysis JSON Schema 正確性、Emotion Detector 準確度。
   - LLM Prompt 模版是否輸出預期欄位。

2. **整合測試 (Integration Tests)**
   - Upload → Analyze → Generate → Compose 完整 pipeline。
   - 確保故事生成 API 在高併發下不阻塞 UI。

3. **邊界案例 (Edge Cases)**
   - 低光、過曝或黑白照片。
   - 長寬比極端（如全景）照片。
   - 無人臉照片的情緒預測 fallback。

4. **性能指標 (Performance Metrics)**

| 指標 | 說明 |
| --- | --- |
| Latency | 單張故事生成時間 < 2 秒 |
| Batch Processing | 多張照片同時處理效能 |
| Memory Usage | LLM API buffer / image loading |
| Cost per Story | API 成本預估，每篇控制在 $0.02 以下 |

## 6. 隱私、安全與合規 (Privacy & Security)

- 所有照片靜態儲存需 AES-256 加密，傳輸採 HTTPS/TLS 1.2 以上。
- 使用者可選「不存圖」，系統僅保留暫時緩存並於生成後清除。
- 符合 GDPR/CCPA 要求，提供資料下載與刪除功能。
- LLM 輸入前進行個資遮罩，避免人名/地點誤傳至第三方 API。

## 7. 多語言與幻覺控制 (Multilingual & Hallucination Control)

- Prompt 設計需預留語言參數，支援 UTF-8/CJK 字元。
- 在 prompt 中加入限制：`Do not invent objects that do not appear in the photo.`
- 生成後執行照片摘要對照檢查，檢測描述與圖像標籤是否一致。
- 對於信心低的輸出，提供「需要人工確認」標記。

## 8. 開發指引與專案治理 (Developer Notes)

1. **版本控制**：採 GitFlow；主幹 (`main`) 只接收可發佈版本。
2. **CI/CD**：推送後自動執行測試、靜態分析、格式檢查。
3. **監控**：導入 APM（Datadog/New Relic）監控 LLM latency 與錯誤率。
4. **紀錄**：重要提示詞、模型版本與 API 參數應記錄在 Config Registry。

## 9. 未來 Roadmap（建議）

- 增加語音敘事，輸出 Audio Storybook。
- 支援多人協作與留言，打造家庭故事牆。
- 引入自動排程（定期寄送故事集給使用者）。
- 開放 Plugin API，讓第三方可自訂風格模版與排版主題。

## 10. 現況與功能缺口 (Implementation Gap Analysis)

| 規劃功能 | 目前狀態 (依程式碼) | 缺口 & 下一步 |
| --- | --- | --- |
| 前後端分離、Vue UI | `app.py` 仍以 Streamlit 實作單頁流程 | 建立 Vue 介面（上傳、設定、預覽）並改以 REST API 串接，完成 CORS 設定與路由規劃 |
| Storybook Composer (PDF/Web/eBook) | 尚未實作排版或匯出模組 | 開發 `Composer Service`，支援 ReportLab/HTML 渲染與檔案快取 |
| 故事版本控制、歷史紀錄 | UI 只顯示即時一次結果，沒有儲存 | 新增後端 `stories` 資料表或 JSON 儲存、前端版本列表 UI |
| 多語言/風格 Tokens 管理 | Style 選單僅含 5 種文字，無語言切換 | 建立 Style/Locale 設定 API，拉齊 Prompt 模板並支援國際化文案 |
| API Gateway & Queue | 模型呼叫在前端同步執行，不可橫向擴充 | 封裝 FastAPI Endpoint、可選 RabbitMQ/Kafka 任務佇列 |
| 隱私與匯出策略 | 暫存檔案寫入 `temp/` 但缺加密與清除策略 | 實作加密儲存、排程清檔、提供「不存圖」選項與審計紀錄 |
| IoT 整合 | 尚無硬體事件或 metadata pipeline | 建立 `iot.ingest` API、規劃裝置註冊與批次上傳流程 |

> 上述缺口需依優先級列入開發排程；建議先完成 Vue + FastAPI 架構遷移，再分模組補齊排版與資料持久化。
