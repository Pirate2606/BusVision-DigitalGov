import cv2
import numpy as np
from tracker import *
import os


tracker = EuclideanDistTracker()

# Detection confidence threshold
conf_threshold = 0.7
nms_threshold = 0.7

# Middle cross line position
middle_line_position = 225
up_line_position = middle_line_position - 15
down_line_position = middle_line_position + 15

# List for store vehicle count information
detected_classNames = []

# Store Coco Names in a list
classesFile = "coco.names"
classNames = open(classesFile).read().strip().split('\n')

# class index for our required detection classes
required_class_index = [2, 3, 7]

# Define random colour for each class
np.random.seed(42)
colors = np.random.randint(0, 255, size=(len(classNames), 3), dtype='uint8')

cwd = os.getcwd()
PATH = os.path.join(os.getcwd(), 'static')
IMAGES_PATH = os.path.join(PATH, 'images')


# Function for finding the center of a rectangle
def find_center(x, y, w, h):
    x1 = int(w/2)
    y1 = int(h/2)
    cx = x+x1
    cy = y+y1
    return cx, cy


# Function for count vehicle
def count_vehicle(box_id, img, center_lane, video_name, lane_violators, real_video):
    class_id, x, y, w, h, id_, index = box_id
    center = find_center(x, y, w, h)
    ix, iy = center
    final_path = os.path.join(IMAGES_PATH, video_name.split(".")[0])
    try:
        os.mkdir(final_path)
    except FileExistsError:
        pass

    if abs(x - int(center_lane)) < 30:
        # if id_ not in lane_violators:
        lane_violators[id_] = [id_, center, center_lane, classNames[class_id]]
        cv2.imwrite(os.path.join(final_path, f"{id_}.jpg"), img)

    return lane_violators


# Function for finding the detected objects from the network output
def post_process(outputs, img, center_lane, video_name, lane_violators, real_video):
    global detected_classNames
    height, width = img.shape[:2]
    boxes = []
    class_ids = []
    confidence_scores = []
    detection = []
    for output in outputs:
        for det in output:
            scores = det[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            if class_id in required_class_index:
                if confidence > conf_threshold:
                    w, h = int(det[2]*width), int(det[3]*height)
                    x, y = int((det[0]*width)-w/2), int((det[1]*height)-h/2)
                    boxes.append([x, y, w, h])
                    class_ids.append(class_id)
                    confidence_scores.append(float(confidence))

    # Apply Non-Max Suppression
    indices = cv2.dnn.NMSBoxes(
        boxes, confidence_scores, conf_threshold, nms_threshold)
    if len(indices) > 0:
        for i in indices.flatten():
            x, y, w, h = boxes[i][0], boxes[i][1], boxes[i][2], boxes[i][3]

            color = [int(c) for c in colors[class_ids[i]]]
            name = classNames[class_ids[i]]
            detected_classNames.append(name)
            # Draw class name and confidence score
            cv2.putText(img, f'{name.upper()} {int(confidence_scores[i]*100)}%',
                        (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

            # Draw bounding rectangle
            cv2.rectangle(img, (x, y), (x + w, y + h), color, 1)
            detection.append(
                [class_ids[i], x, y, w, h, required_class_index.index(class_ids[i])])

    # Update the tracker for each object
    boxes_ids = tracker.update(detection)
    for box_id in boxes_ids:
        lane_violators = count_vehicle(box_id, img, center_lane, video_name, lane_violators, real_video)

    return lane_violators
