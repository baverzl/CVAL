from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtMultimedia import *
from PyQt5.QtWidgets import *

from qtclasses.videowidgetsurface import VideoWidgetSurface
from utils.shape import Shape
from utils.lib import distance

CURSOR_DEFAULT = Qt.ArrowCursor
CURSOR_POINT   = Qt.PointingHandCursor
CURSOR_DRAW    = Qt.CrossCursor
CURSOR_MOVE    = Qt.ClosedHandCursor
CURSOR_GRAB    = Qt.OpenHandCursor

class VideoWidget(QWidget):
    def __init__(self, mediaPlayer, parent=None):
        super(VideoWidget, self).__init__(parent)

        self.shapes = []
        self.current = None
        self.selectedShape = None
        self.selectedShapeCopy = None
        self.lineColor = QColor(0, 0, 255)
        self.line = Shape(line_color=self.lineColor)

        self.hShape = None
        self.hVertex = None


        # self.setAutoFillBackground(False)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        # self.setAttribute(Qt.WA_PaintOnScreen, True)
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

        # super(VideoWidget, self).paintEvent(event)

        print('media player position:', self.mediaPlayer.position())

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
                if self.begin and self.end:
                    self.surface.setBoundingBoxCoords((self.begin, self.end))
            self.surface.paint(painter)
        else:
            painter.fillRect(event.rect(), self.palette().window())

    def resizeEvent(self, event):
        QWidget.resizeEvent(self, event)
        self.surface.updateVideoRect()

    def outOfPixmap(self):
        pass

    def boundedMoveVertex(self):
        index, shape = self.hVertex, self.hShape
        point = shape[index]
        if self.outOfPixmap(pos):
            pos = self.intersectionPoint(point, pos)

        shiftPos = pos - point
        shape.move

    def selectedVertex(self):
        return self.hVertex is not None

    def mousePressEvent(self, event):

        #self.overrideCursor(CURSOR_DRAW)
        if event.button() == Qt.LeftButton:
            if self.drawing():
                if self.current and self.current.reachMaxPoints() is False:
                    initPos = self.current[0]
                    minX = initPos.x()
                    minY = initPos.y()
                    targetPos = self.line[1]
                    maxX = targetPos.x()
                    maxY = targetPos.y()
                    self.current.addPoint(QPointF(maxX, minY))
                    self.current.addPoint(targetPos)
                    self.current.addPoint(QPointF(minX, maxY))
                    self.current.addPoint(initPos)
                    self.line[0] = self.current[-1]
                    if self.current.isClosed():
                        self.finalise()
                elif not self.outOfPixmap(pos):
                    self.current = Shape()
                    self.current.addPoint(pos)
                    self.line.points = [pos, pos]
                    self.setHiding()
                    self.drawingPolygon.emit(True)
                    self.update()
            else:
                self.selectShapePoint(pos)
                self.prevPoint = pos
                self.repaint()
        elif ev.button() == Qt.RightButton and self.editing():
            self.selectShapePoint(pos)
            self.prevPoint = pos
            self.repaint()


        self.update()

    def mouseMoveEvent(self, event):

        #if Qt.LeftButton & event.buttons():
            #if self.selectedVertex():
            #    self.boundedMoveVertex(pos)
            #    self.shaepd

        self.end = event.pos()
        self.update()

    def mouseReleaseEvent(self, event):

        if event.button() == Qt.LeftButton:
            self.overrideCursor(CURSOR_DEFAULT)
            self.begin = event.pos()
            self.end = event.pos()
        elif event.button() == Qt.RightButton:
            menu = self.menus[0]
            menu.exec_(self.mapToGlobal(event.pos()))

        self.update()

    def wheelEvent(self, ev):
        point = ev.angleDelta()
        if point.y() > 0:
            self.mediaPlayer.setPosition(self.mediaPlayer.position() + 100)
        else:
            self.mediaPlayer.setPosition(self.mediaPlayer.position() - 100)

        ev.accept()

    def restoreCursor(self):
        QApplication.restoreOverrideCursor()

    def overrideCursor(self, cursor):
        self.restoreCursor()
        self._cursor = cursor
        QApplication.setOverrideCursor(cursor)