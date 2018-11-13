import numpy as np

def convertQImageToMat(incomingImage):
    '''Converts a QImage into an opencv MAT format'''

    # Format-enum : http://doc.qt.io/qt-5/qimage.html#Format-enum
    incomingImage = incomingImage.convertToFormat(4) # to QImage::Format_RGB32 which is a 32-bit RGB format (0xffRRGGBB).

    width = incomingImage.width()
    height = incomingImage.height()

    ptr = incomingImage.bits()
    ptr.setsize(incomingImage.byteCount())
    arr = np.array(ptr).reshape(height, width, 4) # Copies the data
    arr = arr[:, :, :3]
    return arr