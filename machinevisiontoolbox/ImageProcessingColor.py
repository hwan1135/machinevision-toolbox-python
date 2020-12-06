#!/usr/bin/env python

import numpy as np
import spatialmath.base.argcheck as argcheck
import cv2 as cv
import matplotlib.path as mpath

import machinevisiontoolbox.color as color

from scipy import interpolate

# import scipy as sp

# from scipy import signal
# from scipy import interpolate

# from collecitons import namedtuple
# from pathlib import Path


class ImageProcessingColorMixin:
    """
    Image processing color operations on the Image class
    """

    def red(self):
        """
        Extract the red plane of a color image

        :raises ValueError: if image is not color
        :return out: greyscale image representing the red image plane
        :rtype: Image instance
        """
        if not self.iscolor:
            raise ValueError('cannot extract color plane from greyscale image')

        out = [im.rgb[:, :, 0] for im in self]
        # out = []
        # for im in self:
        #     out.append(im.image[:, :, 0])
        return self.__class__(out)

    def green(self):
        """
        Extract the green plane of a color image

        :raises ValueError: if image is not color
        :return out: greyscale image representing the green image plane
        :rtype: Image instance
        """
        if not self.iscolor:
            raise ValueError('cannot extract color plane from greyscale image')

        out = [im.rgb[:, :, 1] for im in self]
        # out = []
        # for im in self:
        #     out.append(im.image[:, :, 1])
        return self.__class__(out)

    def blue(self):
        """
        Extract the blue plane of a color image

        :raises ValueError: if image is not color
        :return out: greyscale image representing the blue image plane
        :rtype: Image instance
        """
        if not self.iscolor:
            raise ValueError('cannot extract color plane from greyscale image')

        out = [im.rgb[:, :, 2] for im in self]
        # out = []
        # for im in self:
        #     out.append(im.image[:, :, 2])
        return self.__class__(out)

    def colorise(self, c=[1, 1, 1]):
        """
        Colorise a greyscale image

        :param c: color to color image :type c: string or rgb-tuple :return
        out: Image  with float64 precision elements ranging from 0 to 1 :rtype:
        Image instance

        - ``IM.color()`` is a color image out, where each color plane is equal
          to image.

        - ``IM.imcolor(c)`` as above but each output pixel is ``c``(3,1) times
          the corresponding element of image.

        Example:

        .. autorun:: pycon

        .. note::

            - Can convert a monochrome sequence (h,W,N) to a color image
              sequence (H,W,3,N).


        :references:

            - Robotics, Vision & Control, Section 10.1, P. Corke,
              Springer 2011.
        """

        c = argcheck.getvector(c).astype(self.dtype)
        c = c[::-1]  # reverse because of bgr

        # make sure im are greyscale
        img = self.mono()

        if img.iscolor is False:
            # only one plane to convert
            # recall opencv uses BGR
            out = [np.dstack((c[0] * im.image,
                              c[1] * im.image,
                              c[2] * im.image))
                   for im in img]
        else:
            raise ValueError(self.image, 'Image must be greyscale')

        return self.__class__(out)

    def showcolorspace(self, cs='xy', N=501, L=90, *args):
        """
        Display spectral locus

        :param cs: 'xy', 'lab', 'ab' or None defines which colorspace to show
        :type xy: string
        :param N: number of points to sample in the x- and y-directions
        :type N: integer, N > 0, default 501
        :param L: length of points to sample for Lab colorspace
        :type L: integer, L > 0, default 90
        :return color: colorspace image
        :rtype color: Image instance

        TODO for now, just return Image of plot

        Example:

        .. autorun:: pycon

        .. note::

            - The colors shown within the locus only approximate the true
              colors, due to the gamut of the display device.

        :references:

            - Robotics, Vision & Control, Chapter 10, P. Corke, Springer 2011.
        """

        # TODO check valid inputs
        # TODO cslist = [None, 'xy', 'ab', 'Lab']
        # which should be defined by cases (showcolorspace.m)

        if not isinstance(cs, str):
            raise TypeError(cs, 'cs must be a string')

        if cs == 'xy':
            #   create axes
            #   create meshgrid
            #   convert xyY to XYZ
            #   convert XYZ to RGB (requires colorspace function)
            #   define boundary
            ex = 0.8
            ey = 0.9
            Nx = round(N * ex)
            Ny = round(N * ey)
            e = 0.01
            # generate colors in xyY color space
            ax = np.linspace(e, ex - e, Nx)
            ay = np.linspace(e, ey - e, Ny)
            xx, yy = np.meshgrid(ax, ay)
            iyy = 1.0 / (yy + 1e-5 * (yy == 0).astype(float))

            # convert xyY to XYZ
            Y = np.ones((Ny, Nx))
            X = Y * xx * iyy
            Z = Y * (1.0 - xx - yy) * iyy
            XYZ = np.dstack((X, Y, Z))

            # TODO replace with color.colorspace(im,conv,**kwargs)
            # (replace starts here)
            # NOTE using cv.COLOR_XYZ2RGB does not seem to work properly
            # it does not do gamma corrections

            XYZ = self.__class__(XYZ)
            BGR = XYZ.colorspace('xyz2bgr')

            # define the boundary
            nm = 1e-9
            lam = np.arange(400, 700, step=5) * nm
            xyz = color.ccxyz(lam)

            xy = xyz[0:, 0:2]

            # make a smooth boundary with spline interpolation
            irange = np.arange(0, xy.shape[0]-1, step=0.1)
            drange = np.linspace(0, xy.shape[0]-1, xy.shape[0])
            fxi = interpolate.interp1d(drange, xy[:, 0], kind='cubic')
            fyi = interpolate.interp1d(drange, xy[:, 1], kind='cubic')
            xi = fxi(irange)
            yi = fyi(irange)
            # add the endpoints
            xi = np.append(xi, xi[0])
            yi = np.append(yi, yi[0])

            # determine which points from xx, yy, are contained within polygon
            # defined by xi, yi
            p = np.stack((xi, yi), axis=-1)
            polypath = mpath.Path(p)

            xxc = xx.flatten('F')
            yyc = yy.flatten('F')
            pts_in = polypath.contains_points(np.stack((xxc, yyc), axis=-1))
            # same for both xx and yy
            colors_in = np.reshape(pts_in, xx.shape, 'F')
            # colors_in_yy = pts_in.reshape(yy.shape)

            # set outside pixels to white
            colorsin3 = np.dstack((colors_in, colors_in, colors_in))
            BGR.image[colorsin3 == 0] = 1.0

            out = BGR.image

        elif (cs == 'ab') or (cs == 'Lab'):
            ax = np.linspace(-100, 100, N)
            ay = np.linspace(-100, 100, N)
            aa, bb = np.meshgrid(ax, ay)

            # convert from Lab to RGB
            avec = argcheck.getvector(aa)
            bvec = argcheck.getvector(bb)

            Lab = np.stack((L * np.ones(avec.shape), avec, bvec), axis=1)
            # TODO currently does not work. OpenCV
            # out = cv.cvtColor(Lab, cv.COLOR_Lab2BGR)

            Lab = self.__class__(Lab)

            BGR = Lab.colorspace('Lab2bgr')

            bgr2d = np.squeeze(BGR.image)
            from machinevisiontoolbox.Image import col2im
            out = col2im(bgr2d, [N, N])
            out = self.__class__(out)
            out = out.float()
            out = out.pixelswitch(BGR.kcircle(np.floor(N / 2)),
                                  np.r_[1.0, 1.0, 1.0])
        else:
            raise ValueError('no or unknown color space provided')

        return self.__class__(out)

    def _invgammacorrection(self, Rg):
        """
        inverse gamma correction

        :param Rg: 2D image
        :type Rg: numpy array, shape (N,M)
        :return: R
        :rtype: numpy array

        - ``_invgammacorrection(Rg)`` returns ``R`` from ``Rg``

        Example:

        .. autorun:: pycon

        .. note::

            - Based on code from Pascal Getreuer 2005-2010
            - And colorspace.m from Peter Corke's Machine Vision Toolbox
        """

        R = np.zeros(Rg.shape)
        a = 0.0404482362771076
        i = np.where(Rg <= a)
        noti = np.where(Rg > a)
        R[i] = Rg[i] / 12.92
        R[noti] = np.real(((Rg[noti] + 0.055) / 1.055) ** 2.4)
        return R

    def _gammacorrection(self, R):
        """
        Gamma correction

        :param R: 2D image
        :type R: numpy array, shape (N,M)
        :return: Rg
        :rtype: numpy array

        - ``_gammacorrection(R)`` returns ``Rg`` from ``R``

        Example:

        .. autorun:: pycon

        .. note::

            - Based on code from Pascal Getreuer 2005-2010
            - And colorspace.m from Peter Corke's Machine Vision Toolbox
        """

        Rg = np.zeros(R.shape)
        a = 0.0031306684425005883
        b = 0.416666666666666667
        i = np.where(R <= a)
        noti = np.where(R > a)
        Rg[i] = R[i] * 12.92
        Rg[noti] = np.real(1.055 * (R[noti] ** b) - 0.055)
        return Rg

    def colorspace(self, conv, **kwargs):
        """
        Transform a color image between color representations

        :param conv: color code for color conversion (OpenCV codes for now)
        :type conv: string (see below)
        :param kwargs: keywords/options for OpenCV's cvtColor
        :type kwargs: name/value pairs
        :return: out
        :rtype: numpy array, shape (N,M) or (N,3)

        - ``IM.colorspace(conv)`` transforms the color representation of image
          where ``conv`` is a string specifying the conversion. The image
          should be a real full double array of size (M,3) or (M,N,3). The
          output is the same size as ``IM``

        ``conv`` tells the source and destination color spaces,
        ``conv`` = 'dest<-src', or alternatively, ``conv`` = 'src->dest'.
        Supported color spaces are
        'RGB'              sRGB IEC 61966-2-1
        'YCbCr'            Luma + Chroma ("digitized" version of Y'PbPr)
        'JPEG-YCbCr'       Luma + Chroma space used in JFIF JPEG
        'YDbDr'            SECAM Y'DbDr Luma + Chroma
        'YPbPr'            Luma (ITU-R BT.601) + Chroma
        'YUV'              NTSC PAL Y'UV Luma + Chroma
        'YIQ'              NTSC Y'IQ Luma + Chroma
        'HSV' or 'HSB'     Hue Saturation Value/Brightness
        'HSL' or 'HLS'     Hue Saturation Luminance
        'HSI'              Hue Saturation Intensity
        'XYZ'              CIE 1931 XYZ
        'Lab'              CIE 1976 L*a*b* (CIELAB)
        'Luv'              CIE L*u*v* (CIELUV)
        'LCH'              CIE L*C*H* (CIELCH)
        'CAT02 LMS'        CIE CAT02 LMS

        .. note::

            - All conversions assume 2 degree observer and D65 illuminant.
              Color space names are case insensitive and spaces are ignored.
              When sRGB is the source or destination, it can be omitted. For
              example 'yuv<-' is short for 'yuv<-rgb'. For sRGB, the values
              should be scaled between 0 and 1.  Beware that transformations
              generally do not constrain colors to be "in gamut." Particularly,
              transforming from another space to sRGB may obtain R'G'B' values
              outside of the [0,1] range.  So the result should be clamped to
              [0,1] before displaying. image(min(max(B,0),1));  lamp B to [0,1]
              and display sRGB (Red Green Blue) is the (ITU-R BT.709
              gamma-corrected) standard red-green-blue representation of colors
              used in digital imaging.  The components should be scaled between
              0 and 1.  The space can be visualized geometrically as a cube.
            - Y'PbPr, Y'CbCr, Y'DbDr, Y'UV, and Y'IQ are related to sRGB by
              linear transformations.  These spaces separate a color into a
              grayscale luminance component Y and two chroma components.  The
              valid ranges of the components depends on the space.
            - HSV (Hue Saturation Value) is related to sRGB by
              H = hexagonal hue angle   (0 <= H < 360),
              S = C/V                   (0 <= S <= 1),
              V = max(R',G',B')         (0 <= V <= 1),
              where C = max(R',G',B') - min(R',G',B').
            - The hue angle H is computed on a hexagon.  The space is
              geometrically a hexagonal cone.
            - HSL (Hue Saturation Lightness) is related to sRGB by
              H = hexagonal hue angle                (0 <= H < 360),
              S = C/(1 - abs(2L-1))                     (0 <= S <= 1),
              L = (max(R',G',B') + min(R',G',B'))/2  (0 <= L <= 1),
              where H and C are the same as in HSV.  Geometrically, the space
              is a double hexagonal cone.
            - HSI (Hue Saturation Intensity) is related to sRGB by
              H = polar hue angle        (0 <= H < 360),
              S = 1 - min(R',G',B')/I    (0 <= S <= 1),
              I = (R'+G'+B')/3           (0 <= I <= 1).
              Unlike HSV and HSL, the hue angle H is computed on a circle
              rather than a hexagon.
            - CIE XYZ is related to sRGB by inverse gamma correction followed
              by a linear transform.  Other CIE color spaces are defined
              relative to XYZ.
            - CIE L*a*b*, L*u*v*, and L*C*H* are nonlinear functions of XYZ.
              The L* component is designed to match closely with human
              perception of lightness.  The other two components describe the
              chroma.
            - CIE CAT02 LMS is the linear transformation of XYZ using the
              MCAT02 chromatic adaptation matrix.  The space is designed to
              model the response of the three types of cones in the human eye,
              where L, M, S, correspond respectively to red ("long"), green
              ("medium"), and blue ("short").

        :references:

            - Robotics, Vision & Control, Chapter 10, P. Corke, Springer 2011.
        """

        # TODO other color cases
        # TODO check conv is valid

        # TODO conv string parsing

        # ensure floats? unsure if cv.cvtColor operates on ints
        imf = self.float()

        out = []
        for im in imf:
            if conv == 'xyz2bgr':
                # note that using cv.COLOR_XYZ2RGB does not seem to work
                BGR_raw = cv.cvtColor(im.bgr, cv.COLOR_XYZ2BGR, **kwargs)

                # desaturate and rescale to constrain resulting RGB values
                # to [0,1]
                B = BGR_raw[:, :, 0]
                G = BGR_raw[:, :, 1]
                R = BGR_raw[:, :, 2]
                add_white = -np.minimum(np.minimum(np.minimum(R, G), B), 0)
                B += add_white
                G += add_white
                R += add_white

                # inverse gamma correction
                B = self._gammacorrection(B)
                G = self._gammacorrection(G)
                R = self._gammacorrection(R)

                out.append(np.dstack((B, G, R)))  # BGR

            elif conv == 'Lab2bgr':
                # convert source from Lab to xyz

                # in colorspace.m, image was parsed into a (251001,1,3)
                labim = np.reshape(im.image,
                                   (im.shape[0], 1, im.shape[1]))

                fY = (labim[:, :, 0] + 16) / 116
                fX = fY + labim[:, :, 1] / 500
                fZ = fY - labim[:, :, 2] / 200
                # cie xyz whitepoint
                WhitePoint = np.r_[0.950456, 1, 1.088754]

                xyz = np.zeros(labim.shape)
                xyz[:, :, 0] = WhitePoint[0] * self._invf(fX)
                xyz[:, :, 1] = WhitePoint[1] * self._invf(fY)
                xyz[:, :, 2] = WhitePoint[2] * self._invf(fZ)

                # then call function again with conv = xyz2bgr
                xyz = self.__class__(xyz)

                out.append(xyz.colorspace('xyz2bgr').image)

            else:
                raise ValueError('other conv options not yet implemented')
                # TODO other color conversion cases
                # out.append(cv.cvtColor(np.float32(im), **kwargs))

        return self.__class__(out)

    def _invf(self, fY):
        """
        Inverse f from colorspace.m
        """
        Y = fY ** 3
        Y[Y < 0.008856] = (fY[Y < 0.008856] - 4 / 29) * (108 / 841)
        return Y

    def gamma(self, gam):
        """
        Inverse gamma correction

        :param gam: string identifying srgb, or scalar to raise the image power
        :type gam: string or float TODO: variable input seems awkward
        :return out: gamma corrected version of image
        :rtype out: Image instance

        - ``IM.gamma(gam)`` is the image with an inverse gamma correction based
          on ``gam`` applied.

        Example:

        .. autorun:: pycon

        .. note::

            - Gamma decoding should be applied to any color image prior to
              colometric operations.
            - The exception to this is colorspace conversion using COLORSPACE
              which expects RGB images to be gamma encoded.
            - Gamma encoding is typically performed in a camera with
              GAMMA=0.45.
            - Gamma decoding is typically performed in the display with
              GAMMA=2.2.
            - For images with multiple planes the gamma correction is applied
              to all planes.
            - For images sequences the gamma correction is applied to all
              elements.
            - For images of type double the pixels are assumed to be in the
              range 0 to 1.
            - For images of type int the pixels are assumed in the range 0 to
              the maximum value of their class.  Pixels are converted first to
              double, processed, then converted back to the integer class.

        :references:

            - Robotics, Vision & Control, Chapter 10, P. Corke, Springer 2011.
        """

        if not (argcheck.isscalar(gam) or isinstance(gam, str)):
            raise TypeError('Warning: gam must be string or scalar')

        imf = self.float()

        out = []
        for im in imf:

            if gam == 'srgb':

                # convert gamma-encoded sRGB to linear tristimulus values

                if im.iscolor:
                    R = self._invgammacorrection(im.rgb[:, :, 0])
                    G = self._invgammacorrection(im.rgb[:, :, 1])
                    B = self._invgammacorrection(im.rgb[:, :, 2])
                    g = np.dstack((R, G, B))
                else:
                    g = self._invgammacorrection(im.image)

                if not im.isfloat:
                    g *= np.iinfo(im.dtype).max
                    g = g.astype(im.dtype)

            else:
                # normal power law:
                if im.isfloat:
                    g = im.image ** gam
                else:
                    # int image
                    maxg = np.float32((np.iinfo(im.dtype).max))
                    g = ((im.astype(np.float32) / maxg) ** gam) * maxg

            out.append(g)

        return self.__class__(out)


# --------------------------------------------------------------------------#
if __name__ == '__main__':

    # test run ImageProcessingColor.py
    print('ImageProcessingColor.py')

    from machinevisiontoolbox.Image import Image

    im = Image('monalisa.png')
    im.disp()

    # imcs = Image.showcolorspace()
    # imcs.disp()

    import code
    code.interact(local=dict(globals(), **locals()))