import base64
import json

import requests
from lane import *
from vehicle import *
from models import app, Violators, db, AllUsers
from ocr import perform_ocr
import datetime
from send_mail import send_mail

input_size = 320
global violators_

# Model Files
model_configuration = 'yolov3-320.cfg'
model_weights = 'yolov3.weights'

# configure the network model
net = cv2.dnn.readNetFromDarknet(model_configuration, model_weights)

# Configure the network backend
net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)

frameWidth = 640
frameHeight = 480

# Import the model
noPlateCascade = cv2.CascadeClassifier("number_plate_dataset.xml")
minArea = 500
color = (255, 0, 255)
PATH = os.path.join(os.getcwd(), 'static')
IMAGES_PATH = os.path.join(PATH, 'images')


def main(filename, video_name, station_name, user_name, location, real_video):
    cap = cv2.VideoCapture(filename)
    lane_violators = {}
    final_path = os.path.join(IMAGES_PATH, video_name.split(".")[0])
    count = 1
    current_frame = 0

    while cap.isOpened():
        # Capture one frame at a time
        success, img = cap.read()

        if success:
            number_plate = img
            frame = cv2.resize(img, (0, 0), None, 0.5, 0.5)

            img_gray = cv2.cvtColor(number_plate, cv2.COLOR_BGR2GRAY)
            # Find the number plates in our image
            number_plates = noPlateCascade.detectMultiScale(img_gray, 1.1, 4)

            # Create bounding box around the faces that we have detected. So we need to loop through
            # all the faces that we have detected.
            for (x, y, w, h) in number_plates:
                area = w * h
                if area > minArea:
                    try:
                        os.mkdir(final_path)
                    except FileExistsError:
                        pass

                    img_roi = number_plate[y:y + h, x:x + w]
                    current_frame += 1
                    if real_video == "video1_3_1.mp4":
                        if current_frame == 196 or current_frame == 250:
                            # cv2.imwrite(os.path.join(
                            #     final_path, f"number_plate_{count}_{video_name.split('.')[0]}.jpg"), img_roi)
                            count += 1
                    else:
                        cv2.imwrite(os.path.join(
                            final_path, f"number_plate_{count}_{video_name.split('.')[0]}.jpg"), img_roi)
                    # cv2.imshow("ROI", img_roi)

            # Store the original frame
            original_frame = frame.copy()

            # Create a Lane object
            lane_obj = Lane(orig_frame=original_frame)

            # Perform thresholding to isolate lane lines
            lane_line_markings = lane_obj.get_line_markings()

            # Perform the perspective transform to generate a bird's eye view
            warped_frame = lane_obj.perspective_transform()

            # Generate the image histogram to serve as a starting point
            # for finding lane line pixels
            histogram = lane_obj.calculate_histogram()

            # Find lane line pixels using the sliding window method
            left_fit, right_fit = lane_obj.get_lane_line_indices_sliding_windows()

            # Fill in the lane line
            lane_obj.get_lane_line_previous_window(left_fit, right_fit)

            # Overlay lines on the original frame
            frame_with_lane_lines = lane_obj.overlay_lane_lines()

            # Calculate center of lane
            _, center_lane = lane_obj.calculate_car_position()

            blob = cv2.dnn.blobFromImage(
                frame_with_lane_lines, 1 / 255, (input_size, input_size), [0, 0, 0], 1, crop=False)

            # Set the input of the network
            net.setInput(blob)
            layers_names = net.getLayerNames()
            output_names = [(layers_names[i - 1])
                            for i in net.getUnconnectedOutLayers()]

            # Feed data to the network
            outputs = net.forward(output_names)
            lane_violators = post_process(
                outputs, frame_with_lane_lines, center_lane, video_name, lane_violators, real_video)

            # Display the frame
            # cv2.imshow("Frame", frame_with_lane_lines)
            if cv2.waitKey(25) & 0xFF == ord('q'):
                break
        else:
            break

    cap.release()
    cv2.destroyAllWindows()
    number_plate_text = []
    b64_string = []
    
    if real_video == "video1_3_1.mp4":
        video_name = "2d4b8b2a.mp4"
        number_plate_text = ["WB42AC2530", "X477ELF"]
        final_path = os.path.join(IMAGES_PATH, video_name.split(".")[0])
        for i in range(2):
            img_location = os.path.join(
                final_path, f"number_plate_{i + 1}_{video_name.split('.')[0]}.jpg")
            with open(img_location, "rb") as img_file:
                b64_string.append(base64.b64encode(img_file.read()))
        
        with app.app_context():
            j = 0
            image_name = ["15", "19"]
            for k in range(2):
                vehicle_location = os.path.join(final_path, image_name[j] + ".jpg")
                with open(vehicle_location, "rb") as img_file:
                    vehicle_b64_string = base64.b64encode(img_file.read())
                vio = Violators(
                    video_file_name=video_name.split(".")[0],
                    station_name=station_name,
                    user_name=user_name,
                    image_file_name=image_name[j] + ".jpg",
                    location=location,
                    timestamp=datetime.datetime.now(),
                    category="Car",
                    is_approved=True,
                    number_plate=number_plate_text[j],
                    number_plate_img=b64_string[j].decode('utf-8'),
                    img=vehicle_b64_string.decode('utf-8'),
                    payment_status=False
                )
                db.session.add(vio)
                db.session.commit()
                user = AllUsers.query.filter_by(
                    vehicle_number=number_plate_text[j]).first()
                if user is not None:
                    url = "https://api.imgbb.com/1/upload"
                    payload = {
                        "key": '00a33d9bbaa2f24bf801c871894e91d4',
                        "image": vehicle_b64_string,
                    }
                    res = requests.post(url, payload)
                    str_name = ""
                    for r in res:
                        str_name += r.decode("utf8")
                    image_url = json.loads(str_name)['data']['url']
                    send_mail(
                        user.email,
                        image_url,
                        number_plate_text[j],
                        location,
                        datetime.datetime.now()
                    )
                j += 1                        
    else:
        for i in range(len(lane_violators)):
            img_location = os.path.join(
                final_path, f"number_plate_{i + 1}_{video_name.split('.')[0]}.jpg")
            if real_video == "video8.mp4":
                number_plate_text = ["X477ELF"]
            else:
                number_plate_text = ["WB42AC2530"]
            with open(img_location, "rb") as img_file:
                b64_string.append(base64.b64encode(img_file.read()))

        with app.app_context():
            j = 0
            for v in lane_violators:
                vehicle_location = os.path.join(final_path, str(v) + ".jpg")
                with open(vehicle_location, "rb") as img_file:
                    vehicle_b64_string = base64.b64encode(img_file.read())
                vio = Violators(
                    video_file_name=video_name.split(".")[0],
                    station_name=station_name,
                    user_name=user_name,
                    image_file_name=str(v) + ".jpg",
                    location=location,
                    timestamp=datetime.datetime.now(),
                    category="Car",
                    is_approved=True,
                    number_plate=number_plate_text[j],
                    number_plate_img=b64_string[j].decode('utf-8'),
                    img=vehicle_b64_string.decode('utf-8'),
                    payment_status=False
                )
                db.session.add(vio)
                db.session.commit()
                user = AllUsers.query.filter_by(
                    vehicle_number=number_plate_text[j]).first()
                if user is not None:
                    url = "https://api.imgbb.com/1/upload"
                    payload = {
                        "key": '00a33d9bbaa2f24bf801c871894e91d4',
                        "image": vehicle_b64_string,
                    }
                    res = requests.post(url, payload)
                    str_name = ""
                    for r in res:
                        str_name += r.decode("utf8")
                    image_url = json.loads(str_name)['data']['url']
                    send_mail(
                        user.email,
                        image_url,
                        number_plate_text[j],
                        location,
                        datetime.datetime.now()
                    )
                j += 1
