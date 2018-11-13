#!/usr/bin/env python3

import os
import sys

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtMultimedia import *
from PyQt5.QtWidgets import *

from qtclasses.videowidget import VideoWidget
from qtclasses.themes import apply_palette
from qtclasses import settings

class cvalWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super(cvalWindow, self).__init__(*args, **kwargs)

        self.showMaximized()

        self.videoLoaded = False

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

        self.videoWidget = VideoWidget(self.mediaPlayer)

        self.mediaPlayer.setVideoOutput(self.videoWidget.videoSurface())

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
        self.open = QAction(QIcon(os.path.join('icons', 'blue-folder-open-document.png')), '&Open...', self, shortcut='Ctrl+O', triggered=self.openFile)

        self.save = QAction('&Save', self, shortcut='Ctrl+S', triggered=self.saveFile)
        self.saveAs = QAction('&Save As', self, shortcut='Ctrl+Shift+S', triggered=self.saveFileAs)


        self.play = QAction(QIcon(os.path.join('icons', 'control.png')), '&Play video...', self, shortcut='F5', triggered=self.playVideo)

        #self.edit = QAction('&Edit Label', )

        self.exit = QAction('&Exit', self, shortcut='Ctrl+Q', triggered=self.close)

    """ Create top menus """
    def createMenus(self):

        self.fileMenu = QMenu('&File', self)
        self.fileMenu.addAction(self.open)
        self.fileMenu.addAction(self.save)
        self.fileMenu.addAction(self.saveAs)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.exit)

        self.toolMenu = QMenu('&Tool', self)
        #self.toolMenu.addAction(self.create)
        #self.toolMenu.addAction(self.delete)
        #self.toolMenu.addAction(self.edit)

        self.helpMenu = QMenu('&Help', self)
        #self.helpMenu.addAction(self.aboutAct)
        #self.helpMenu.addAction(self.aboutQtAct)

        self.menuBar().addMenu(self.fileMenu)
        self.menuBar().addMenu(self.toolMenu)
        self.menuBar().addMenu(self.helpMenu)


    def createToolbars(self):
        
        # Toolbar
        self.file_toolbar = QToolBar('File')
        self.file_toolbar.setIconSize(QSize(14, 14))
        self.addToolBar(self.file_toolbar)

        self.file_toolbar.addAction(self.open)
        self.file_toolbar.addAction(self.play)
  

    def openFile(self):
        fileName, _ = QFileDialog.getOpenFileName(self, 'Open File', '', 'Video Files(*.avi *.mp4 *.webm);;')

        if fileName:
            self.mediaPlayer.setMedia(
                    QMediaContent(QUrl.fromLocalFile(fileName)))

        self.play.setEnabled(True)
        self.videoLoaded = True


    def saveFile(self):
        pass

    def saveFileAs(self):
        pass

    # with Tracking function
    def playVideo(self):

        if self.videoLoaded is False:
            return

        if self.mediaPlayer.state() == QMediaPlayer.StoppedState or self.mediaPlayer.state() == QMediaPlayer.PausedState:
            # object detection + tracking starts
            self.play.setIcon(QIcon(os.path.join('icons', 'control-pause.png')))
            self.mediaPlayer.play()
        else:
            self.play.setIcon(QIcon(os.path.join('icons', 'control.png')))
            self.mediaPlayer.pause()

        # StoppedState means the mediaPlayer reverts back to the origin.

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
    app.setApplicationName(settings.__window_title__)
    apply_palette(app, 'fusion dark')

    cval_win = cvalWindow()
    cval_win.show()
    app.exec_()

if __name__ == '__main__':
    
    sys.exit(GUIMain())
