from pathlib import Path
import pandas as pd
import config


def init_logger(path: str) -> None:
    """Create log file with headers if not exists."""
    columns = ["scene", "art", "status", "W_t", "H_t", "dx", "dy", "error"]
    if not Path(path).exists():
        pd.DataFrame(columns=columns).to_csv(path, index=False)


def log_entry(scene: str, art: str, status: str, params: dict) -> None:
    """Append one log line to csv."""
    data = {
        "scene": scene,
        "art": art,
        "status": status,
        "W_t": params.get("W_t", ""),
        "H_t": params.get("H_t", ""),
        "dx": params.get("dx", ""),
        "dy": params.get("dy", ""),
        "error": params.get("error", ""),
    }
    df = pd.DataFrame([data])
    header = not Path(config.LOG_PATH).exists()
    df.to_csv(config.LOG_PATH, mode="a", header=header, index=False)
