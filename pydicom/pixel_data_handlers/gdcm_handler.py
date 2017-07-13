import sys
have_numpy = True
try:
    import numpy
except ImportError:
    have_numpy = False
    raise

have_gdcm = True
try:
    import gdcm
except ImportError:
    have_gdcm = False
    raise

def get_pixeldata(self):
    # read the file using GDCM
    # FIXME this should just use self.PixelData instead of self.filename
    #       but it is unclear how this should be achieved using GDCM
    gdcm_image_reader = gdcm.ImageReader()
    gdcm_image_reader.SetFileName(self.filename)
    if not gdcm_image_reader.Read():
        raise TypeError("GDCM could not read DICOM image")
    gdcm_image = gdcm_image_reader.GetImage()

    # determine the correct numpy datatype
    gdcm_numpy_typemap = {
        gdcm.PixelFormat.INT8:     numpy.int8,
        gdcm.PixelFormat.UINT8:    numpy.uint8,
        gdcm.PixelFormat.UINT16:   numpy.uint16,
        gdcm.PixelFormat.INT16:    numpy.int16,
        gdcm.PixelFormat.UINT32:   numpy.uint32,
        gdcm.PixelFormat.INT32:    numpy.int32,
        gdcm.PixelFormat.FLOAT32:  numpy.float32,
        gdcm.PixelFormat.FLOAT64:  numpy.float64
    }
    gdcm_pixel_format = gdcm_image.GetPixelFormat().GetScalarType()
    if gdcm_pixel_format in gdcm_numpy_typemap:
        numpy_dtype = gdcm_numpy_typemap[gdcm_pixel_format]
    else:
        raise TypeError('{0} is not a GDCM supported '
                        'pixel format'.format(gdcm_pixel_format))

    # GDCM returns char* as type str. Under Python 2 `str` are
    # byte arrays by default. Python 3 decodes this to
    # unicode strings by default.
    # The SWIG docs mention that they always decode byte streams
    # as utf-8 strings for Python 3, with the `surrogateescape`
    # error handler configured.
    # Therefore, we can encode them back to their original bytearray
    # representation on Python 3 by using the same parameters.
    pixel_bytearray = gdcm_image.GetBuffer()
    if sys.version_info >= (3, 0):
        pixel_bytearray = pixel_bytearray.encode("utf-8",
                                                 "surrogateescape")

    # if GDCM indicates that a byte swap is in order, make
    #   sure to inform numpy as well
    if gdcm_image.GetNeedByteSwap():
        numpy_dtype = numpy_dtype.newbyteorder('S')

    # Here we need to be careful because in some cases, GDCM reads a
    # buffer that is too large, so we need to make sure we only include
    # the first n_rows * n_columns * dtype_size bytes.

    n_bytes = self.Rows * self.Columns * numpy.dtype(numpy_dtype).itemsize

    if len(pixel_bytearray) > n_bytes:

        # We make sure that all the bytes after are in fact zeros
        padding = pixel_bytearray[n_bytes:]
        if numpy.any(numpy.fromstring(padding, numpy.byte)):
            pixel_bytearray = pixel_bytearray[:n_bytes]
        else:
            # We revert to the old behavior which should then result
            #   in a Numpy error later on.
            pass
    return pixel_bytearray
