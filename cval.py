#!/usr/bin/env python3

import os
import sys

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtPrintSupport import *
from PyQt5.QtMultimedia import *
from PyQt5.QtMultimediaWidgets import *

import pdb

import os
import sys
import uuid

import cv2

class VideoWidgetSurface(QAbstractVideoSurface):

    def __init__(self, widget, parent=None):
        super(VideoWidgetSurface, self).__init__(parent)

        self.widget = widget
        self.imageFormat = QImage.Format_Invalid

        self.is_drawing = False

    def supportedPixelFormats(self, handleType=QAbstractVideoBuffer.NoHandle):
        formats = [QVideoFrame.PixelFormat()]
        if (handleType == QAbstractVideoBuffer.NoHandle):
            for f in [QVideoFrame.Format_RGB32,
                    QVideoFrame.Format_ARGB32,
                    QVideoFrame.Format_ARGB32_Premultiplied,
                    QVideoFrame.Format_RGB565,
                    QVideoFrame.Format_RGB555
                     ]:
                formats.append(f)
        return formats

    def isFormatSupported(self, _format):
        imageFormat = QVideoFrame.imageFormatFromPixelFormat(_format.pixelFormat())
        size = _format.frameSize()
        _bool = False
        if (imageFormat != QImage.Format_Invalid and not
            size.isEmpty() and
            _format.handleType() == QAbstractVideoBuffer.NoHandle):
            _bool = True
        return _bool

    def start(self, _format):
        imageFormat = QVideoFrame.imageFormatFromPixelFormat(_format.pixelFormat())
        size = _format.frameSize()
        if (imageFormat != QImage.Format_Invalid and not size.isEmpty()):
            self.imageFormat = imageFormat
            self.imageSize = size
            self.sourceRect = _format.viewport()
            QAbstractVideoSurface.start(self, _format)
            self.widget.updateGeometry()
            self.updateVideoRect()
            return True
        else:
            return False

    def stop(self):
        self.currentFrame = QVideoFrame()
        self.targetRect = QRect()
        QAbstractVideoSurface.stop(self)
        self.widget.update()

    def present(self, frame):
        if (self.surfaceFormat().pixelFormat() != frame.pixelFormat() or
            self.surfaceFormat().frameSize() != frame.size()):
            self.setError(QAbstractVideoSurface.IncorrectFormatError)
            self.stop()
            return False
        else:
            self.currentFrame = frame
            self.widget.repaint(self.targetRect)
            return True

    def videoRect(self):
        return self.targetRect

    def updateVideoRect(self):
        size = self.surfaceFormat().sizeHint()
        # boundedTo(): Returns a size holding the minimum width and height of this size and the given otherSize
        size.scale(self.widget.size().boundedTo(size), Qt.KeepAspectRatio)
        self.targetRect = QRect(QPoint(0, 0), size);
        # center(): Returns the center point of the rectangle
        # moveCenter(): Moves the rectangle, leaving the center point at the given position. The rectangle's size is unchanged.
        self.targetRect.moveCenter(self.widget.rect().center())

    def setBoundingBoxCoords(self, coords):
        self.coords = coords
        self.is_drawing = True

    def paint(self, painter):
        # Maps the contents of a video frame to system (CPU addressable) memory.
        # Returns true if the frame was mapped to memory in the given mode and false otherwise

        if (self.currentFrame.map(QAbstractVideoBuffer.ReadOnly)):
            # Return the world transformation matrix.
            oldTransform = painter.transform()

        # Paint upside down
        if (self.surfaceFormat().scanLineDirection() == QVideoSurfaceFormat.BottomToTop):
            painter.scale(1, -1); # rotate according to x-axis
            painter.translate(0, -self.widget.height()) # translate -widget.height

        image = QImage(self.currentFrame.bits(),
                        self.currentFrame.width(),
                        self.currentFrame.height(),
                        self.currentFrame.bytesPerLine(),
                        self.imageFormat
                        )

        # Draws the rectangular portion source of the given image into the target rectangle in the paint device
        painter.drawImage(self.targetRect, image, self.sourceRect)

        # NOTE: The order of drawing is important.
        if self.is_drawing:
            self._color = QColor(100, 10, 40, 100)
            brush = QBrush(self._color)
            painter.setBrush(brush)
            painter.drawRect(QRect(self.coords[0], self.coords[1]))
            self.is_drawing = False

        # Sets the world transformation matrix. If combine is true, the specified transform is combined with the current matrix; otherwise it replaces the current matrix.
        painter.setTransform(oldTransform)

        self.currentFrame.unmap()

class VideoWidget(QWidget):

    def __init__(self, mediaPlayer, parent=None):
        super(VideoWidget, self).__init__(parent)

        self.begin = None
        self.end = None

        #self.setAutoFillBackground(False)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        #self.setAttribute(Qt.WA_PaintOnScreen, True)
        palette = self.palette()
        palette.setColor(QPalette.Background, Qt.black)
        self.setPalette(palette)
        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        self.surface = VideoWidgetSurface(self)

        self.mediaPlayer = mediaPlayer

        self.show()

    def videoSurface(self):
        return self.surface

    def closeEvent(self, event):
        del self.surface

    def sizeHint(self):
        return self.surface.surfaceFormat().sizeHint()

    def paintEvent(self, event):

#        super(VideoWidget, self).paintEvent(event)

        if self.begin is False:
            return

        painter = QPainter(self)
        if (self.surface.isActive()):
            videoRect = self.surface.videoRect()
            # Qt 5: need to convert a rect to a region
            videoRegion = QRegion(videoRect)
            if not videoRect.contains(event.rect()):
                region = event.region()
                # Qt4 : region.subtract(videoRect) ; subtracting a rect from a region is possible, but not in Qt5
                region -= videoRegion
                # Qt4 : brush = self.palette().background()
                brush = self.palette().brush(QPalette.Background)
                painter.setBrush(brush)
                for rect in region.rects():
                    painter.drawRect(rect)
            if self.mediaPlayer.state() == QMediaPlayer.PausedState:
                self.surface.setBoundingBoxCoords((self.begin, self.end))
            self.surface.paint(painter)
        else:
            painter.fillRect(event.rect(), self.palette().window())

    def resizeEvent(self, event):
        QWidget.resizeEvent(self, event)
        self.surface.updateVideoRect()
         
    def mousePressEvent(self, event):

        if event.button() == Qt.LeftButton:
            self.begin = event.pos()
            self.end = event.pos()

        self.update()

    def mouseMoveEvent(self, event):
        self.end = event.pos()
        self.update()

    def mouseReleasedEvent(self, event):

        if event.button() == Qt.LeftButton:
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
        fileName, _ = QFileDialog.getOpenFileName(self, 'Open File', '', 'Video Files(*.avi *.mp4 *.webm);;')

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
    
        if self.mediaPlayer.state() == QMediaPlayer.PausedState:
            self.mediaPlayer.play()
        else:
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
