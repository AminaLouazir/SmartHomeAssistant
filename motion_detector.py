import cv2

cap = cv2.VideoCapture(0)  # or replace with IP camera URL
ret, frame1 = cap.read()
ret, frame2 = cap.read()

diff = cv2.absdiff(frame1, frame2)
gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
blur = cv2.GaussianBlur(gray, (5,5), 0)
_, thresh = cv2.threshold(blur, 20, 255, cv2.THRESH_BINARY)
dilated = cv2.dilate(thresh, None, iterations=3)
contours, _ = cv2.findContours(dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

if len(contours) > 0:
    print("motion")
else:
    print("no motion")

cap.release()
