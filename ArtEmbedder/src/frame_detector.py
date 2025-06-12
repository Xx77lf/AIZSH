import cv2
import numpy as np
from typing import Dict
import config


def detect_frame_corners(img: np.ndarray, params: Dict) -> np.ndarray:
    """Detect frame corners from image and return 4x2 array of points."""
    eps = params.get("PERSPECTIVE_EPS", config.PERSPECTIVE_EPS)

    # Segment possible frame regions
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2Lab)
    L, a, b = cv2.split(lab)
    _, mask_white = cv2.threshold(L, 200, 255, cv2.THRESH_BINARY)

    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    mask_green = cv2.inRange(hsv, (40, 40, 40), (80, 255, 255))
    mask_blue = cv2.inRange(hsv, (100, 40, 40), (140, 255, 255))

    mask = cv2.bitwise_or(mask_white, cv2.bitwise_or(mask_green, mask_blue))

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        raise ValueError("No frame detected")

    c = max(contours, key=cv2.contourArea)
    peri = cv2.arcLength(c, True)
    approx = cv2.approxPolyDP(c, eps * peri, True)

    if len(approx) != 4:
        rect = cv2.minAreaRect(c)
        box = cv2.boxPoints(rect)
    else:
        box = approx.reshape(-1, 2)

    center = np.mean(box, axis=0)
    def angle(p):
        return np.arctan2(p[1] - center[1], p[0] - center[0])

    box_sorted = np.array(sorted(box, key=angle), dtype=np.float32)
    return box_sorted
