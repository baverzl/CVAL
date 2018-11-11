#!/usr/bin/env python3

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtPrintSupport import *
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtMultimediaWidgets import QVideoWidget

import pdb

import os
import sys
import uuid

import cv2

class BoundingBox():

    def __init__(self):
        pass

class VideoDisplayWidget(QVideoWidget):

    def __init__(self, mediaPlayer):
        super(QVideoWidget, self).__init__()

        self.begin = None
        self.end = None

        self.mediaPlayer = mediaPlayer

#        self.setAlignment(Qt.AlignCenter)
       
        self.show()

    def paintEvent(self, event):
        super(QVideoWidget, self).paintEvent(event)

        if self.begin is None:
            return

        print(self.begin, self.end)
        qp = QPainter(self)
        br = QBrush(QColor(100, 10, 40, 100))
        qp.setBrush(br)
        qp.drawRect(QRect(self.begin, self.end))

    def mousePressEvent(self, event):
        self.begin = event.pos()
        self.end = event.pos()
        self.update()

    def mouseMoveEvent(self, event):
        self.end = event.pos()
        self.update()

    def mouseReleasedEvent(self, event):
        self.begin = event.pos()
        self.end = event.pos()
        self.update()

    def wheelEvent(self, ev):
        point = ev.angleDelta()
        if point.y() > 0:
            self.mediaPlayer.setPosition(self.mediaPlayer.position() + 100)
        else:
            self.mediaPlayer.setPosition(self.mediaPlayer.position() - 100)

        ev.accept()


class cvalWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super(cvalWindow, self).__init__(*args, **kwargs)

        self.showMaximized()
        MainLayout = QHBoxLayout()

        ProjectPanel = QWidget()
        ProjectPanelVLayout = QVBoxLayout()
        self.AnnotationLabelList = QFrame()
        self.AnnotationLabelList.setFrameShape(QFrame.StyledPanel)
        ProjectPanelVLayout.addWidget(self.AnnotationLabelList)
        ProjectPanel.setLayout(ProjectPanelVLayout)

        # Set media player
        self.mediaPlayer = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        #self.mediaPlayer.stateChanged.connect(self.mediaStateChanged)
        self.mediaPlayer.durationChanged.connect(self.durationChanged)
        self.mediaPlayer.positionChanged.connect(self.positionChanged)
        self.mediaPlayer.bufferStatusChanged.connect(self.bufferingProgress)
        self.mediaPlayer.error.connect(self.displayErrorMessage)

        if not self.mediaPlayer.isAvailable():
            QMessageBox.warning(self, "Service not available",
                        "The QMediaPlayer object does not have a valid service.\n"
                        "Please check the media service plugins are installed.")

#        self.VideoDisplayPanel = VideoDisplayPanel()
        self.videoWidget = VideoDisplayWidget(self.mediaPlayer)
        #print(dir(self.videoWidget))
#        self.videoWidget.setVisible(False)
#        self.VideoDisplayPanel.setFrameShape(QFrame.StyledPanel)

        self.mediaPlayer.setVideoOutput(self.videoWidget)

        self.videoPlayPanel = QFrame()
        self.videoPlayPanel.setFrameShape(QFrame.StyledPanel)

        videoPlayPanelLayout = QHBoxLayout()
        
        self.timeSlider = QSlider(self.videoPlayPanel)
        self.timeSlider.setOrientation(Qt.Horizontal)
        self.timeSlider.setObjectName('timeSlider')
#        self.timeSlider.setRange(0, self.mediaPlayer.duration() / 1000)
        self.timeSlider.sliderMoved.connect(self.seek)

        self.labelDuration = QLabel()
        videoPlayPanelLayout.addWidget(self.timeSlider)
        videoPlayPanelLayout.addWidget(self.labelDuration)
        self.videoPlayPanel.setLayout(videoPlayPanelLayout)

        splitter1 = QSplitter(Qt.Horizontal)
        splitter1.addWidget(ProjectPanel)
        splitter1.addWidget(self.videoWidget)
        leftPanelSize = self.frameGeometry().width() * 0.15
        rightPanelSize = self.frameGeometry().width() - leftPanelSize
        splitter1.setSizes([leftPanelSize, rightPanelSize])

        splitter2 = QSplitter(Qt.Vertical)
        splitter2.addWidget(splitter1)
        splitter2.addWidget(self.videoPlayPanel)
        topPanelSize = self.frameGeometry().height() * 0.75
        bottomPanelSize = self.frameGeometry().height() - topPanelSize
        splitter2.setSizes([topPanelSize, bottomPanelSize])

        MainLayout.addWidget(splitter2)

        centralWidget = QWidget(self)
        centralWidget.setLayout(MainLayout)

        self.setCentralWidget(centralWidget)

        self.createStatusbars()
        self.createActions()
        self.createMenus()
        self.createToolbars()

        self.setGeometry(50, 50, 800, 800)
        self.setWindowTitle('CVAL (Computer Vision-aided Annotation Labeling) - v1.0.0')
        self.show()

    """Set bottom status bar"""
    def createStatusbars(self):
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)

    """Define actions"""
    def createActions(self):
        self.openAct = QAction(QIcon(os.path.join('images', 'blue-folder-open-document.png')), '&Open...', self, shortcut='Ctrl+O', triggered=self.openFile)

        self.exitAct = QAction('&Exit', self, shortcut='Ctrl+Q',
                triggered=self.close)

        self.videoPlayAct = QAction(QIcon(os.path.join('images', 'control.png')), '&Play video...', self, shortcut='F5', triggered=self.play)

    """ Create top menus """
    def createMenus(self):

        self.fileMenu = QMenu('&File', self)
        self.fileMenu.addAction(self.openAct)
        #self.fileMenu.addAction(self.printAct)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.exitAct)

        #self.helpMenu = QMenu('&Help', self)
        #self.helpMenu.addAction(self.aboutAct)
        #self.helpMenu.addAction(self.aboutQtAct)

        self.menuBar().addMenu(self.fileMenu)
        #self.menuBar().addMenu(self.helpMenu)


    def createToolbars(self):
        
        # Toolbar
        self.file_toolbar = QToolBar('File')
        self.file_toolbar.setIconSize(QSize(14, 14))
        self.addToolBar(self.file_toolbar)

        self.file_toolbar.addAction(self.openAct)
        self.file_toolbar.addAction(self.videoPlayAct)
  

    def openFile(self):
        fileName, _ = QFileDialog.getOpenFileName(self, 'Open File', '', 'Video Files(*.avi *.mp4);;')

        if fileName:
            self.mediaPlayer.setMedia(
                    QMediaContent(QUrl.fromLocalFile(fileName)))

        self.videoPlayAct.setEnabled(True)
#            self.playButton.setEnabled(True)

        # self.VideoDisplayPanel.setPixmap(pixmap)
        # self.VideoDisplayPanel.resize(pixmap.width(), pixmap.height())
        # self.VideoDisplayPanel.getDisplayBox().setPixmap(pixmap)
        # self.VideoDisplayPanel.resize(pixmap.width(), pixmap.height())

        # self.timer = QTimer()
        # self.timer.timeout.connect(self.getNextFrame)
        # self.timer.start(1000.0/30)

    def play(self):
    
        if self.mediaPlayer.state() == QMediaPlayer.StoppedState:
            self.mediaPlayer.play()
        else:
            self.mediaPlayer.pause()

    def seek(self, seconds):
        self.mediaPlayer.setPosition(seconds * 1000)

    def updateTimeLapse(self, position):
        duration = self.duration
        if position or duration:
            currentTime = QTime((position/3600)%60, (position/60)%60,
                    position%60, (position * 1000) % 1000)
            totalTime = QTime((duration/3600)%60, (duration/60)%60,
                    duration%60, (duration * 1000) % 1000)
            format = 'hh:mm:ss' if duration > 3600 else 'mm:ss'
            tStr = currentTime.toString(format) + " / " + totalTime.toString(format)
        else:
            tStr = ""

        self.labelDuration.setText(tStr)

    def positionChanged(self, position):
        position /= 1000

        if not self.timeSlider.isSliderDown():
            self.timeSlider.setValue(position)

        self.updateTimeLapse(position)

    def durationChanged(self, duration):
        duration /= 1000

        # duration in ms
        self.duration = duration
        self.timeSlider.setMaximum(duration)

    def bufferingProgress(self, progress):
        self.setStatusInfo("Buffering %d%" % progress)
    
    def displayErrorMessage(self):
        self.statusBar.showMessage("Error: " + self.mediaPlayer.errorString())

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.close()
        elif e.key() == Qt.Key_F11:
            if self.isMaximized():
                self.showNormal()
            else:
                self.showMaximized()
    

def GUIMain():

    app = QApplication(sys.argv)
    app.setApplicationName('CVAL::')
    app.setStyle('Fusion')

    # Fusion dark palette from https://gist.github.com/QuantumCD/6245215.
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ToolTipBase, Qt.white)
    palette.setColor(QPalette.ToolTipText, Qt.white)
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, Qt.black)
    app.setPalette(palette)
    app.setStyleSheet("QToolTip { color: #ffffff; background-color: #2a82da; border: 1px solid white; }")

    cval_win = cvalWindow()
    cval_win.show()
    app.exec_()

if __name__ == '__main__':
    
    sys.exit(GUIMain())
