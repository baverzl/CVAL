from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtMultimedia import *

import os
from utils.convertUtils import convertQImageToMat
from models.refinedet_sort.refinedet import RefineDet

class VideoWidgetSurface(QAbstractVideoSurface):

    def __init__(self, widget, parent=None):
        super(VideoWidgetSurface, self).__init__(parent)

        self.widget = widget
        self.imageFormat = QImage.Format_Invalid

        self.is_drawing = False

        import configparser

        basedirname = 'models/refinedet_sort'

        config = configparser.ConfigParser()
        config.read(os.path.join(basedirname, 'model.ini'))

        # Add tracking functionality to RefineDet
        self.detector = RefineDet(config, tracked=True)

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
        self.targetRect = QRect(QPoint(0, 0), size)
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
            painter.scale(1, -1) # rotate according to x-axis
            painter.translate(0, -self.widget.height()) # translate -widget.height

        image = QImage(self.currentFrame.bits(),
                        self.currentFrame.width(),
                        self.currentFrame.height(),
                        self.currentFrame.bytesPerLine(),
                        self.imageFormat
                       )

        # Draws the rectangular portion source of the given image into the target rectangle in the paint device
        painter.drawImage(self.targetRect, image, self.sourceRect)
        matImage = convertQImageToMat(image)

        dets = self.detector.feed(matImage).filter(0.4).track().getOutputs()
        for det in dets:
            print('track id:', det.track_id)
            print('track coords:', det.xmin, det.ymin, det.xmax, det.ymax)
            print('color:', det.color)
            alpha_transparency = 100
            color = QColor(det.color[0], det.color[1], det.color[2], alpha_transparency)
            brush = QBrush(color)
            painter.setBrush(brush)
            leftTop, rightBottom  = (QPoint(det.xmin + self.targetRect.x(), det.ymin + self.targetRect.y()),
                                     QPoint(det.xmax + self.targetRect.x(), det.ymax + self.targetRect.y()))
            text_position = QPoint(det.xmin + self.targetRect.x(), det.ymin + self.targetRect.y() - 10)
            painter.drawText(text_position, str(det.track_id))
            painter.drawRect(QRect(leftTop, rightBottom))

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