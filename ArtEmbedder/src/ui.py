import os
import threading
from pathlib import Path
from typing import List

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QListWidget, QVBoxLayout, QHBoxLayout,
    QGroupBox, QSpinBox, QDoubleSpinBox, QPushButton, QTextEdit,
    QProgressBar, QApplication, QLabel
)
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QDragEnterEvent, QDropEvent
from PyQt5.Qt import QDesktopServices

import config
import pipeline


class DropListWidget(QListWidget):
    def __init__(self, single: bool = False):
        super().__init__()
        self.setAcceptDrops(True)
        self.single = single

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            if self.single:
                self.clear()
            for url in event.mimeData().urls():
                path = url.toLocalFile()
                if os.path.isfile(path):
                    if self.single and self.count() > 0:
                        self.takeItem(0)
                    self.addItem(path)
            event.acceptProposedAction()
        else:
            super().dropEvent(event)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("画芯自动嵌入工具")
        self.resize(800, 600)
        self._setup_ui()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout()
        central.setLayout(main_layout)

        # Scene list and art list
        self.scene_list = DropListWidget()
        self.art_list = DropListWidget(single=True)
        main_layout.addWidget(self.scene_list)
        main_layout.addWidget(self.art_list)

        # Right side layout for params and controls
        right_layout = QVBoxLayout()
        main_layout.addLayout(right_layout)

        param_group = QGroupBox("参数")
        param_layout = QVBoxLayout()
        param_group.setLayout(param_layout)
        right_layout.addWidget(param_group)

        self.feather_spin = QSpinBox()
        self.feather_spin.setRange(0, 50)
        self.feather_spin.setValue(config.FEATHER_RADIUS)
        self.eps_spin = QDoubleSpinBox()
        self.eps_spin.setRange(0.0, 1.0)
        self.eps_spin.setSingleStep(0.01)
        self.eps_spin.setValue(config.PERSPECTIVE_EPS)

        param_layout.addWidget(QLabel("羽化半径"))
        param_layout.addWidget(self.feather_spin)
        param_layout.addWidget(QLabel("透视精度 eps"))
        param_layout.addWidget(self.eps_spin)

        ctrl_layout = QHBoxLayout()
        right_layout.addLayout(ctrl_layout)

        self.start_btn = QPushButton("开始合成")
        self.stop_btn = QPushButton("停止")
        self.open_btn = QPushButton("打开输出目录")
        ctrl_layout.addWidget(self.start_btn)
        ctrl_layout.addWidget(self.stop_btn)
        ctrl_layout.addWidget(self.open_btn)

        self.progress = QProgressBar()
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        right_layout.addWidget(self.progress)
        right_layout.addWidget(self.log_view)

        self.start_btn.clicked.connect(self.start_process)
        self.open_btn.clicked.connect(self.open_output)

    def open_output(self):
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(Path(config.OUTPUT_DIR).absolute())))

    def start_process(self):
        scene_paths = [self.scene_list.item(i).text() for i in range(self.scene_list.count())]
        art_path = self.art_list.item(0).text() if self.art_list.count() > 0 else None
        if not scene_paths or not art_path:
            self.log_view.append("Please drag in scene images and one art image.")
            return
        params = {
            "FEATHER_RADIUS": self.feather_spin.value(),
            "PERSPECTIVE_EPS": self.eps_spin.value()
        }
        thread = threading.Thread(target=pipeline.run_batch, args=(scene_paths, art_path, params, self.progress_cb))
        thread.start()

    def progress_cb(self, idx: int, total: int, message: str):
        self.progress.setMaximum(total)
        self.progress.setValue(idx)
        self.log_view.append(message)

