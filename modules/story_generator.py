import json
import os
from typing import Dict, List

import requests
from dotenv import load_dotenv

# 載入 API Key
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

LANGUAGE_HINTS = {
    "zh-TW": "Use Traditional Chinese (繁體中文) phrasing and avoid Simplified characters.",
    "en": "Use natural English prose.",
}


def _request_gemini(prompt_text: str) -> str:
    if not api_key:
        raise RuntimeError("請先在 .env 中設定 GOOGLE_API_KEY")

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        "gemini-2.5-flash:generateContent"
        f"?key={api_key}"
    )
    payload = {"contents": [{"parts": [{"text": prompt_text}]}]}
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    if response.status_code != 200:
        raise RuntimeError(f"API Error {response.status_code}: {response.text}")

    try:
        text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
        return text
    except (KeyError, IndexError) as exc:  # pragma: no cover - guard for API schema change
        raise RuntimeError("Gemini 回傳格式改變，無法解析") from exc


def _extract_json_block(text: str) -> Dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("No JSON object found")
    return json.loads(text[start : end + 1])


def generate_storybook(photos: List[Dict], style: str, language: str = "en") -> Dict:
    """
    根據多張照片的分析結果生成故事書結構（panels + summary）
    """
    language_hint = LANGUAGE_HINTS.get(language, language)
    context_lines = []
    for idx, photo in enumerate(photos, start=1):
        analysis = photo.get("analysis", {})
        caption = analysis.get("caption", "")
        emotion = analysis.get("emotion", "")
        colors = ", ".join(analysis.get("color_profile", {}).get("dominant_colors", []))
        tags = ", ".join(analysis.get("tags", []))
        context_lines.append(
            f"Photo {idx} (id={photo.get('image_id')}): scene='{caption}', emotion='{emotion}', "
            f"colors={colors}, tags={tags}"
        )
    context_block = "\n".join(context_lines)

    prompt_text = f"""
You are an empathetic storyteller. Craft a cohesive narrative that weaves together all provided photos.
Context:
{context_block}

Task:
- Produce a storybook where each photo becomes a panel with a short title and 2-4 sentence body.
- Keep tone/style as: {style}.
- Language hint: {language_hint}. Always use Traditional Chinese characters when writing Chinese.
- Ensure the number of panels equals the number of photos and preserve the order.

Return strictly valid JSON with the following structure:
{{
  "panels": [
    {{"image_id": "<original image id>", "title": "...", "body": "..."}}
  ],
  "summary": "Overall takeaway in {language_hint}"
}}
"""

    try:
        raw_text = _request_gemini(prompt_text)
        story_json = _extract_json_block(raw_text)
    except Exception as exc:
        print(f"LLM 解析失敗，使用 fallback：{exc}")
        panels = [
            {
                "image_id": photo.get("image_id", ""),
                "title": f"Photo {idx}",
                "body": photo.get("analysis", {}).get("caption", "Snapshot"),
            }
            for idx, photo in enumerate(photos, start=1)
        ]
        return {"panels": panels, "summary": "AI Story Album"}

    return story_json


def generate_story(caption, emotion, style, language="en"):
    """
    維持舊版介面，將單張圖片轉為故事文字
    """
    storybook = generate_storybook(
        photos=[{"image_id": "temp", "analysis": {"caption": caption, "emotion": emotion}}],
        style=style,
        language=language,
    )
    return "\n".join(panel.get("body", "") for panel in storybook.get("panels", []))
