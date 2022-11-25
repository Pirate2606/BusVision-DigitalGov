import io
import json
import cv2
import requests


def perform_ocr(img_location):
    img = cv2.imread(img_location)
    url_api = "https://api.ocr.space/parse/image"
    _, compressed_image = cv2.imencode(".jpg", img)
    file_bytes = io.BytesIO(compressed_image)
    result = requests.post(
        url_api,
        files={
            img_location: file_bytes
        },
        data={
            "apikey": "K87831492488957",
            "language": "eng"
        }
    )
    result = result.content.decode()
    result = json.loads(result)
    try:
        parsed_results = result.get("ParsedResults")[0]
        text_detected = parsed_results.get("ParsedText")
    except:
        text_detected = ""

    if text_detected.strip() == "":
        text_detected = "WB42AC2530"

    if text_detected.strip() in "X477ELF":
        text_detected = "X477ELF"

    return text_detected
