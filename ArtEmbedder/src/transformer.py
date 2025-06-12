from pathlib import Path
import numpy as np
import cv2
from typing import Tuple, Dict
import config


def compute_transform(W_s: int, H_s: int, dst_pts: np.ndarray, params: Dict) -> Tuple[np.ndarray, float, float, float, float]:
    """Compute perspective transform for embedding art into dst_pts."""
    xs = dst_pts[:, 0]
    ys = dst_pts[:, 1]
    W_t = float(xs.max() - xs.min())
    H_t = float(ys.max() - ys.min())

    s = min(W_t / W_s, H_t / H_s)
    W_p = W_s * s
    H_p = H_s * s
    dx = (W_t - W_p) / 2.0
    dy = (H_t - H_p) / 2.0

    alpha = dx / W_t if W_t else 0
    beta = dy / H_t if H_t else 0

    Q = []
    for i in range(4):
        p_i = dst_pts[i]
        p_next = dst_pts[(i + 1) % 4]
        p_prev = dst_pts[(i - 1) % 4]
        q = p_i + alpha * (p_next - p_i) + beta * (p_prev - p_i)
        Q.append(q)
    Q = np.array(Q, dtype=np.float32)

    src_pts = np.array([[0, 0], [W_s, 0], [W_s, H_s], [0, H_s]], dtype=np.float32)
    H_mat = cv2.getPerspectiveTransform(src_pts, Q)
    return H_mat, W_t, H_t, dx, dy


def warp_and_blend(canvas: np.ndarray, art: np.ndarray, H: np.ndarray, params: Dict) -> np.ndarray:
    """Warp art using matrix H and blend into canvas."""
    h_c, w_c = canvas.shape[:2]

    warped = cv2.warpPerspective(art, H, (w_c, h_c))

    src_pts = np.array([[0, 0], [art.shape[1], 0], [art.shape[1], art.shape[0]], [0, art.shape[0]]], dtype=np.float32)
    dst_pts_embedded = cv2.perspectiveTransform(src_pts.reshape(-1, 1, 2), H).reshape(4, 2)

    mask = np.zeros((h_c, w_c), dtype=np.uint8)
    cv2.fillConvexPoly(mask, dst_pts_embedded.astype(np.int32), 255)

    radius = params.get("FEATHER_RADIUS", config.FEATHER_RADIUS)
    ksize = max(1, int(radius) * 2 + 1)
    mask_blur = cv2.GaussianBlur(mask, (ksize, ksize), 0)
    mask_norm = mask_blur.astype(np.float32) / 255.0

    result = canvas.copy()
    for c in range(3):
        result[:, :, c] = warped[:, :, c] * mask_norm + canvas[:, :, c] * (1 - mask_norm)

    return result
