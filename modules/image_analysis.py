from functools import lru_cache
import os
from typing import Dict, List

import numpy as np
from PIL import Image
import torch
from transformers import BlipForConditionalGeneration, BlipProcessor

ENABLE_DEEPFACE = os.getenv("ENABLE_DEEPFACE", "false").lower() == "true"
DeepFace = None
if ENABLE_DEEPFACE:
    try:
        from deepface import DeepFace  # type: ignore
    except Exception as exc:  # pragma: no cover - optional dependency
        DeepFace = None
        print(f"DeepFace unavailable, fallback to neutral emotion: {exc}")


@lru_cache(maxsize=1)
def load_caption_model():
    """
    以 LRU cache 快取 BLIP 模型，避免多次載入造成延遲。
    """
    try:
        print("正在載入 BLIP 模型...")
        processor = BlipProcessor.from_pretrained(
            "Salesforce/blip-image-captioning-base", use_safetensors=True
        )
        model = BlipForConditionalGeneration.from_pretrained(
            "Salesforce/blip-image-captioning-base", use_safetensors=True
        )
        return processor, model
    except BaseException as exc:  # pragma: no cover - fallback when offline
        print(f"⚠️ BLIP 模型載入失敗：{exc}")
        return None, None


def _extract_color_profile(image: Image.Image) -> Dict:
    """
    以簡化方式估算亮度、飽和度與主要色調。
    """
    rgb_image = image.convert("RGB")
    np_rgb = np.asarray(rgb_image) / 255.0
    brightness = float(np.mean(np_rgb))

    hsv_image = image.convert("HSV")
    np_hsv = np.asarray(hsv_image) / 255.0
    saturation = float(np.mean(np_hsv[:, :, 1]))
    hue_channel = np_hsv[:, :, 0]

    # 依 hue 粗略分成 6 個色區，求出主色
    bins = [0, 1 / 6, 2 / 6, 3 / 6, 4 / 6, 5 / 6, 1.01]
    counts, _ = np.histogram(hue_channel, bins=bins)
    dominant_index = int(np.argmax(counts))
    color_lookup = ["red", "yellow", "green", "cyan", "blue", "magenta"]
    dominant_color = color_lookup[min(dominant_index, len(color_lookup) - 1)]

    return {
        "brightness": round(brightness, 3),
        "saturation": round(saturation, 3),
        "dominant_colors": [dominant_color],
    }


def _guess_tags_from_caption(caption: str) -> List[str]:
    tokens = [
        token.strip(".,!?:;\"'").lower()
        for token in caption.split()
        if len(token.strip(".,!?:;\"'")) >= 3
    ]
    unique_tokens = []
    for token in tokens:
        if token not in unique_tokens:
            unique_tokens.append(token)
    return unique_tokens[:5]


def analyze_image_content(image_path: str) -> Dict:
    """
    輸入圖片路徑，回傳包含 caption/emotion/color_profile/tags 的 JSON 物件。
    """
    processor, model = load_caption_model()
    raw_image = Image.open(image_path).convert("RGB")

    if processor and model:
        inputs = processor(raw_image, return_tensors="pt")
        with torch.no_grad():
            output_ids = model.generate(**inputs)
        caption = processor.decode(output_ids[0], skip_special_tokens=True)
    else:
        width, height = raw_image.size
        orientation = "landscape" if width >= height else "portrait"
        caption = f"A {orientation} photo ({width}x{height}) captured locally."

    emotion = "neutral (emotion model unavailable)"
    if DeepFace:
        try:
            analysis = DeepFace.analyze(
                img_path=image_path, actions=["emotion"], enforce_detection=False
            )
            if isinstance(analysis, list):
                emotion = analysis[0]["dominant_emotion"]
            else:
                emotion = analysis["dominant_emotion"]
        except Exception as exc:
            print(f"DeepFace 分析失敗：{exc}")
            emotion = "neutral (no face detected)"

    color_profile = _extract_color_profile(raw_image)
    tags = _guess_tags_from_caption(caption)

    return {
        "caption": caption,
        "emotion": emotion,
        "color_profile": color_profile,
        "tags": tags,
    }
