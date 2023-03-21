import cv2
import keras_ocr
import re
from PIL import Image
import io
import numpy as np
from keras_ocr.detection import Detector

# Instantiate the keras_ocr pipeline
pipeline = keras_ocr.pipeline.Pipeline()

def get_column_boxes(img, column_pairs):
    w, h = img.size
    column_boxes = []
    for pair in column_pairs:
        x1 = int(w * pair[0])
        x2 = int(w * pair[1])
        column_boxes.append([(x1, 0), (x2, h)])
    return column_boxes

def extract_text_from_columns(img, column_boxes):
    pipeline = keras_ocr.pipeline.Pipeline()
    detector = Detector()
    column_texts = []
    for box in column_boxes:
        x1, y1 = box[0]
        x2, y2 = box[1]
        cropped_img = np.asarray(img.crop((x1, y1, x2, y2)).convert('RGB'))
        detected = detector.detect([cropped_img])[0]
        cropped_img_pil = Image.fromarray(cropped_img)
        print(Image)
        print(cropped_img_pil)
        text = pipeline.recognize([cropped_img])[0]
        column_texts.append([word[0] for word in text])
    return column_texts

def perform_ocr_keras_ocr(image_path):
    # Load the image
    with open(image_path, 'rb') as f:
        image_bytes = f.read()
    image = Image.open(io.BytesIO(image_bytes))

    # Define the column boundaries as pairs of percentages
    column_pairs = [
        (0, 0.08261245674740483),
        (0.14143598615916955, 0.33780276816608995),
        (0.33780276816608995, 0.4329584775086505),
        (0.4329584775086505, 0.5341695501730104),
        (0.5341695501730104, 0.6362456747404844),
        (0.6362456747404844, 0.7331314878892734),
        (0.7331314878892734, 0.847318339100346),
        (0.847318339100346, 1)
    ]

    # Get column bounding boxes
    column_boxes = get_column_boxes(image, column_pairs)

    # Extract text from columns
    column_texts = extract_text_from_columns(image, column_boxes)

    return column_texts, image

def draw_boxes(img):
    # Get OCR data (including bounding boxes)
    img_array = np.asarray(img.convert('RGB'))
    data = pipeline.recognize([img_array])[0]

    # Draw the bounding boxes
    for text, box in data:
        x1, y1 = box[0]
        x2, y2 = box[2]
        img_array = np.asarray(img.convert('RGB'))
        img_array = cv2.rectangle(img_array, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
        img = Image.fromarray(img_array)

    # Save the image with boxes
    img_array = np.asarray(img.convert('RGB'))
    cv2.imwrite("output_image_keras_ocr.png", img_array)

def process_line(column_texts):
    # Join the parts of each column text by spaces
    joined_text = " ".join(column_texts)

    # Split the joined text by comma to get the values
    rank, player_name, score, kills, deaths, assists, healing, damage = joined_text.split(",")

    score = score.replace(" ", "").replace(",", "") if score else '0'
    kills = kills.replace("z", "7").replace("o", "0") if kills else '0'
    deaths = deaths.replace("z", "7").replace("o", "0") if deaths else '0'
    assists = assists.replace("z", "7").replace("o", "0") if assists else '0'
    healing = healing.replace("o", "0").replace("z", "7") if healing else '0'
    damage = damage.replace("o", "0").replace("z", "7") if damage else '0'

    return [rank, player_name, score, kills, deaths, assists, healing, damage]

def main():
    image_path = "image.png"
    column_texts, img = perform_ocr_keras_ocr(image_path)
    draw_boxes(img)

    # Print the parsed data and store it in a dictionary
    results = []
    row_count = max(len(column) for column in column_texts)
    for row in range(row_count):
        line_texts = [column[row] if row < len(column) else '' for column in column_texts]
        processed_line = process_line(line_texts)
        print(processed_line)

        if processed_line is not None and len(processed_line) == 8 and processed_line[1]:
            result = {
                'rank': processed_line[0],
                'player_name': processed_line[1],
                'score': processed_line[2],
                'kills': (processed_line[3]),
                'deaths': (processed_line[4]),
                'assists': (processed_line[5]),
                'healing': (processed_line[6]),
                'damage': (processed_line[7])
            }
            results.append(result)

    # Print the results as a dictionary
    for result in results:
        print(result)

if __name__ == "__main__":
    main()