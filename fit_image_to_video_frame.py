from pathlib import Path

from PIL import Image
from rapidocr_onnxruntime import RapidOCR


BASE_DIR = Path(__file__).resolve().parent
IMAGE_PATH = BASE_DIR / "Example images" / "ImageKickOffClassic.png"

# Tight crop around the Match timer in the top-left scoreboard.
TIMER_CROP = (55, 66, 104, 98)
OCR = RapidOCR()


def _preprocess_timer_crop(image_path: Path) -> Image.Image:
    # High-contrast grayscale crop improves OCR speed and stability.
    with Image.open(image_path) as source:
        crop = source.crop(TIMER_CROP).convert("L")
    return crop.point(lambda value: 255 if value > 150 else 0)


def extract_match_timer(image_path=IMAGE_PATH):
    image = _preprocess_timer_crop(Path(image_path))

    # Timer location is fixed, so recognition-only can avoid detection overhead.
    try:
        result, _ = OCR(image, use_det=False, use_cls=False, use_rec=True)
    except TypeError:
        # Fallback for versions that do not support these kwargs.
        result, _ = OCR(image)

    if not result:
        return ""

    text_parts = []
    for item in result:
        # Full pipeline: [box, text, score], recognition-only: [text, score].
        if isinstance(item, (list, tuple)) and item:
            if isinstance(item[0], str):
                text_parts.append(item[0])
            elif len(item) > 1 and isinstance(item[1], str):
                text_parts.append(item[1])

    text = "".join(text_parts)
    return "".join(character for character in text if character.isdigit() or character == ":")


def main():
    return extract_match_timer()


if __name__ == "__main__":
    print(main())
