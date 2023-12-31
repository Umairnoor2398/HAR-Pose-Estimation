import cv2
import numpy as np
import time
import PoseModule as pm
from flask import Flask, render_template, Response

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


cap = cv2.VideoCapture(0)
detector = pm.poseDetector()
count = 0
pcount = 0
cv2.namedWindow('Image', cv2.WND_PROP_FULLSCREEN)
cv2.setWindowProperty('Image', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
old_coords = []


def find_difference(old, new):
    x1, y1 = old
    x2, y2 = new
    diff1 = abs(x1-x2)
    diff2 = abs(y1-y2)
    # print(diff1,diff2)
    return (diff1+diff2)/2


def check_pose(old_coords, top, bottom, left, right, height, thresh=13):
    if top[1] > height:
        return 'Sitting', 0

    if len(old_coords) == 0:
        old_coords.append([top, bottom, left, right])
        return None, 0
    else:
        top_old, bottom_old, left_old, right_old = old_coords[0]
        diff1 = find_difference(top_old, top)
        diff2 = find_difference(bottom_old, bottom)
        diff3 = find_difference(left_old, left)
        diff4 = find_difference(right_old, right)
        avg = np.mean(np.array([diff1, diff2, diff3, diff4]))
        print(avg)
        if avg > thresh:
            return 'Moving', avg
        else:
            return 'Standing', avg


def generate_frames():
    count = 0
    old_coords = []
    while True:
        success, img = cap.read()
        count += 1
        img = detector.findPose(img, False)
        lmList = detector.findPosition(img, False)
        if len(lmList) != 0:
            _ = detector.findAngle(img, 12, 14, 16)
            _ = detector.findAngle(img, 11, 13, 15)
            _ = detector.findAngle(img, 14, 12, 24)
            _ = detector.findAngle(img, 13, 11, 23)
            _ = detector.findAngle(img, 12, 24, 26)
            _ = detector.findAngle(img, 11, 23, 25)
            _ = detector.findAngle(img, 24, 26, 28)
            _ = detector.findAngle(img, 23, 25, 27)
            top = detector.findAngle(img, 11, 12, 14, draw=False)
            bottom = detector.findAngle(img, 28, 32, 30, draw=False)
            left = detector.findAngle(img, 16, 18, 20, draw=False)
            right = detector.findAngle(img, 15, 17, 19, draw=False)
            h, w = img.shape[:2]
            h_line = int(0.6 * h)
            pose, avg = check_pose(
                old_coords, top[1], bottom[1], left[1], right[1], h_line)
            if count == 20:
                old_coords = []
                old_coords.append([top[1], bottom[1], left[1], right[1]])
                count = 0

        cv2.line(img, (0, h_line), (w, h_line), (0, 255, 0), 4)
        if pose:
            cv2.rectangle(img, (0, 10), (300, 80), (0, 0, 0), -1)
            cv2.putText(img, 'Action: {}'.format(pose), (0, 50),
                        cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 0), 4)

        _, buffer = cv2.imencode('.jpg', img)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':
    app.run(debug=True)
