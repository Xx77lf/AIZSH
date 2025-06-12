from pathlib import Path
from typing import List, Dict
import cv2
import config
from frame_detector import detect_frame_corners
from transformer import compute_transform, warp_and_blend
from logger import init_logger, log_entry


def run_batch(scene_paths: List[str], art_path: str, params: Dict, progress_cb):
    art = cv2.imread(art_path)
    if art is None:
        raise ValueError(f"Cannot read art image: {art_path}")
    W_s, H_s = art.shape[1], art.shape[0]
    init_logger(config.LOG_PATH)
    for idx, canvas_path in enumerate(scene_paths, 1):
        try:
            canvas = cv2.imread(canvas_path)
            if canvas is None:
                raise ValueError(f"Cannot read scene image: {canvas_path}")
            pts = detect_frame_corners(canvas, params)
            H_mat, W_t, H_t, dx, dy = compute_transform(W_s, H_s, pts, params)
            result = warp_and_blend(canvas, art, H_mat, params)
            out_name = f"{Path(art_path).stem}_{Path(canvas_path).stem}.jpg"
            out_path = Path(config.OUTPUT_DIR) / out_name
            cv2.imwrite(str(out_path), result)
            log_entry(Path(canvas_path).name, Path(art_path).name, "OK", {"W_t": W_t, "H_t": H_t, "dx": dx, "dy": dy})
            progress_cb(idx, len(scene_paths), f"{out_name} OK")
        except Exception as e:
            log_entry(Path(canvas_path).name, Path(art_path).name, "ERROR", {"error": str(e)})
            progress_cb(idx, len(scene_paths), f"{Path(canvas_path).name} ERROR: {e}")
