from pathlib import Path

from PIL import Image
from rapidocr_onnxruntime import RapidOCR


BASE_DIR = Path(__file__).resolve().parent
IMAGE_PATH = BASE_DIR / "Example images" / "ImageKickOffClassic.png"

# Tight crop around the Match timer in the top-left scoreboard.
TIMER_CROP = (55, 66, 104, 98)
OCR = RapidOCR()


def extract_match_timer(image_path=IMAGE_PATH):
    image = Image.open(image_path).crop(TIMER_CROP)
    result, _ = OCR(image)

    if not result:
        return ""

    text = "".join(item[1] for item in result)
    return "".join(character for character in text if character.isdigit() or character == ":")


def main():
    return extract_match_timer()


if __name__ == "__main__":
    print(main())
