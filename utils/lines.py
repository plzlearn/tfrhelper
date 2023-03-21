import cv2
import numpy as np

def detect_vertical_lines(img, threshold=100, min_line_length=50, max_line_gap=5):
    edges = cv2.Canny(img, 50, 150)
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold, minLineLength=min_line_length, maxLineGap=max_line_gap)

    vertical_lines = []
    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            if abs(x1 - x2) < 10:  # Adjust this value to be more or less strict on vertical lines
                vertical_lines.append([(x1, y1), (x2, y2)])

    return vertical_lines

def get_column_percentages(vertical_lines, img_width):
    x_coords = sorted([line[0][0] for line in vertical_lines])
    column_percents = [0] + [x / img_width for x in x_coords] + [1]
    return column_percents

def merge_close_lines(column_percents, min_distance_percent):
    merged_percents = [column_percents[0]]
    
    for i in range(1, len(column_percents)):
        if column_percents[i] - merged_percents[-1] > min_distance_percent:
            merged_percents.append(column_percents[i])
        else:
            merged_percents[-1] = (merged_percents[-1] + column_percents[i]) / 2
            
    return merged_percents

def main():
    image_path = "imagelines.png"
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    _, img_binary = cv2.threshold(img, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)

    vertical_lines = detect_vertical_lines(img_binary)
    column_percents = get_column_percentages(vertical_lines, img.shape[1])

    min_distance_percent = 0.02  # Set this value based on the minimum distance between columns you expect
    column_percents = merge_close_lines(column_percents, min_distance_percent)

    print(column_percents)

if __name__ == "__main__":
    main()