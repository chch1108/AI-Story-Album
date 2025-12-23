from pathlib import Path
from PIL import Image

from modules.image_analysis import analyze_image_content

img_path = Path('temp/test_image.jpg')
img_path.parent.mkdir(parents=True, exist_ok=True)

Image.new('RGB', (256, 256), color=(200, 180, 150)).save(img_path)
print('Running analyze...')
result = analyze_image_content(str(img_path))
print(result)
