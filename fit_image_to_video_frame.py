# Import Path for working with file and directory paths.
from pathlib import Path

# Import time so we can measure how long OCR takes.
import time

# Import Pillow's Image class for opening, cropping, and processing images.
from PIL import Image

# Import the RapidOCR OCR engine.
from rapidocr_onnxruntime import RapidOCR


# Get the absolute path of the directory containing this Python script.
BASE_DIR = Path(__file__).resolve().parent

# Build the path to the screenshot containing the FC 26 timer.
IMAGE_PATH = BASE_DIR / "Example images" / "ImageKickOffClassic.png"


# Define the exact rectangle containing the match timer.
# Format: (left, top, right, bottom).
TIMER_CROP = (55, 66, 104, 98)

# Create the RapidOCR engine once so we don't have to initialize it
# every time extract_match_timer() is called.
OCR = RapidOCR()


# Define the exact timer crop once so both file-based and image-based
# OCR paths use the same coordinates.
def _preprocess_timer_crop_from_image(image: Image.Image) -> Image.Image:

    # Crop only the timer area using the coordinates defined above.
    # Then convert the cropped image to grayscale ("L" mode).
    crop = image.crop(TIMER_CROP).convert("L")

    # Convert the grayscale image into a black-and-white image.
    #
    # Every pixel is examined:
    # - If its brightness is greater than 150, make it white (255).
    # - Otherwise, make it black (0).
    #
    # This increases contrast between the timer digits and the background.
    return crop.point(lambda value: 255 if value > 150 else 0)


# Define a helper function that takes an image path and returns
# a preprocessed Pillow image containing only the timer.
def _preprocess_timer_crop(image_path: Path) -> Image.Image:

    # Open the source image.
    # The "with" statement automatically closes the image afterwards.
    with Image.open(image_path) as source:
        return _preprocess_timer_crop_from_image(source)


# Define the function responsible for extracting the timer text.
#
# If no image_source is provided, it uses IMAGE_PATH defined above.
def extract_match_timer(image_source=IMAGE_PATH):

    # Accept either a file path or an in-memory Pillow image.
    if isinstance(image_source, Image.Image):

        # Reuse the same crop logic for video frames and screenshots.
        image = _preprocess_timer_crop_from_image(image_source)

    else:

        # Convert the supplied path into a Path object and preprocess
        # the image by cropping it, converting it to grayscale,
        # and applying the black/white threshold.
        image = _preprocess_timer_crop(Path(image_source))

    # Because we already know exactly where the timer is,
    # we can try to disable OCR's text detection stage.
    #
    # use_det=False -> don't search for where text is.
    # use_cls=False -> don't perform text orientation classification.
    # use_rec=True  -> perform text recognition.
    try:
        result, _ = OCR(
            image,
            use_det=False,
            use_cls=False,
            use_rec=True
        )

    # Some versions of RapidOCR may not accept those arguments.
    # If that happens, fall back to the normal OCR call.
    except TypeError:
        result, _ = OCR(image)

    # If OCR didn't recognize anything, return an empty string.
    if not result:
        return ""

    # Create an empty list that will contain the recognized text pieces.
    text_parts = []

    # Go through every item returned by RapidOCR.
    for item in result:

        # RapidOCR can return different result formats.
        #
        # This checks that the item is either a list or tuple,
        # and that it isn't empty.
        #
        # Full pipeline may return:
        #     [box, text, score]
        #
        # Recognition-only may return:
        #     [text, score]
        if isinstance(item, (list, tuple)) and item:

            # If the first element is a string, it is the recognized text.
            #
            # Example:
            #     ["45", 0.98]
            #
            # item[0] == "45"
            if isinstance(item[0], str):

                # Add the recognized text to our list.
                text_parts.append(item[0])

            # Otherwise, if the second element exists and is a string,
            # assume the second element contains the recognized text.
            #
            # Example:
            #     [bounding_box, "45", 0.98]
            #
            # item[1] == "45"
            elif len(item) > 1 and isinstance(item[1], str):

                # Add the recognized text to our list.
                text_parts.append(item[1])

    # Combine all recognized text pieces into one string.
    #
    # Example:
    #     ["4", "5"] -> "45"
    #
    # The empty string "" means that nothing is inserted between
    # the individual pieces.
    text = "".join(text_parts)

    # Clean the OCR result.
    #
    # Keep only:
    # - digits (0-9)
    # - the colon character (:)
    #
    # This removes OCR mistakes such as letters or other symbols.
    #
    # Example:
    #     "4S:3O" -> "4:3"
    #
    # because S and O are not digits.
    return "".join(
        character
        for character in text
        if character.isdigit() or character == ":"
    )


# Define the main function of the program.
def main():

    # Run the timer extraction twice.
    for i in range(2):

        # Record the exact time immediately before starting OCR.
        start_time = time.perf_counter()

        # Extract the timer from the screenshot.
        timer_text = extract_match_timer()

        # Calculate how much time has passed since start_time.
        elapsed_time = time.perf_counter() - start_time

        # Print:
        # - which run this was
        # - how many seconds it took
        # - what timer value OCR extracted
        #
        # Example output:
        # Run 1: 0.012345 s, Extracted timer: '45:32'
        print(
            f"Run {i + 1}: "
            f"{elapsed_time:.6f} s, "
            f"Extracted timer: '{timer_text}'"
        )

    # Return 0 to indicate that the program finished successfully.
    return 0


# This condition checks whether this file is being executed directly.
#
# If you run:
#     python script.py
#
# __name__ will be "__main__", so main() will run.
#
# If this file is imported by another Python file,
# main() will NOT automatically run.
if __name__ == "__main__":

    # Run the main function.
    #
    # SystemExit uses the value returned by main() as the program's
    # exit status. Returning 0 means successful execution.
    raise SystemExit(main())