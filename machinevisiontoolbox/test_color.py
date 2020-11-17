#!/usr/bin/env python

import numpy as np
import numpy.testing as nt
import unittest
import machinevisiontoolbox.color as color

from pathlib import Path
from machinevisiontoolbox.Image import Image


class TestColor(unittest.TestCase):

    def test_blackbody(self):

        e = color.blackbody(500e-9, 4000)
        self.assertAlmostEqual(e, 2.86512308e+12, delta=1e4)

        e = color.blackbody([400e-9, 500e-9], 4000)
        self.assertEqual(len(e), 2)
        self.assertAlmostEqual(e[0], 1.44662486e+12, delta=1e4)
        self.assertAlmostEqual(e[1], 2.86512308e+12, delta=1e4)

    def test_loadspectrum(self):

        data_dir = Path.cwd() / 'data'

        nm = 1e-9
        lam = np.linspace(400, 700, 30) * nm
        brick = color.loadspectrum(lam, (data_dir / 'redbrick').as_posix())
        self.assertEqual(brick.s.shape, (30, 1))
        nt.assert_array_almost_equal(lam, brick.lam)

        cone = color.loadspectrum(lam, (data_dir / 'cones').as_posix())
        self.assertEqual(cone.s.shape, (30, 3))

        # tests outside of interpolation range
        lam2 = np.linspace(300, 1000, 50) * nm
        solar = color.loadspectrum(lam2, (data_dir / 'solar').as_posix())
        self.assertEqual(solar.s.shape, (50, 1))

        # lam_water = np.linspace(400, 700, 30) * nm
        # water = color.loadspectrum(lam_water,
        #                     (data_dir / 'water').as_posix())

    def test_chromaticity(self):

        # these tests just check if the code runs and the output is the correct
        # shape
        rg = color.lambda2rg(555e-9)
        self.assertEqual(rg.shape, (1, 2))

        rg = color.lambda2rg(lam=np.array([555e-9, 666e-9]),
                             e=np.array([4, 1, 2]))
        self.assertEqual(rg.shape, (1, 2))

        xy = color.lambda2xy(555e-9)
        self.assertEqual(xy.shape, (1, 2))

        xy = color.lambda2rg(lam=np.c_[555e-9, 666e-9],
                             e=np.r_[4, 1, 2])
        self.assertEqual(xy.shape, (1, 2))

        # create Bayer pattern
        im = np.zeros((2, 2, 3))
        # 0 - red channel, 1 - green channel, 2 - blue channel
        im[0, 0, 0] = 1  # top left = red
        im[0, 1, 1] = 1  # top right = green
        im[1, 0, 1] = 1  # bottom left = green
        im[1, 1, 2] = 1  # bottom right = blue

        cc = color.tristim2cc(im)
        cc_ans = np.array([[[1, 0], [0, 1]], [[0, 1], [0, 0]]])
        nt.assert_array_almost_equal(cc, cc_ans)

        # chromaticity is invariant to intensity (im/2)
        cc = color.tristim2cc(im/2)
        cc_ans = np.array([[[1, 0], [0, 1]], [[0, 1], [0, 0]]])
        nt.assert_array_almost_equal(cc, cc_ans)

        #lam = np.arange(400, 700) * 1e-9
        #rg = color.lambda2rg(lam)

        wcc = color.tristim2cc(np.r_[1, 1, 1])
        self.assertEqual(wcc.shape, (1, 2))

    def test_showcolorspace(self):

        # test it runs and is the correct shape
        # may also be able to test values of specific coordinates?
        imcs = Image().showcolorspace('xy')
        self.assertEqual(imcs.shape, (451, 401, 3))

        imcs = Image().showcolorspace('ab')
        self.assertEqual(imcs.shape, (501, 501, 3))

    def test_gamma(self):

        a = Image(np.array([[0.4]]))
        g = a.gamma(0.5)
        nt.assert_array_almost_equal(g.image * g.image, a.image)

        a = Image(np.array([[64.0]]))
        g = a.gamma(0.5)
        nt.assert_array_almost_equal(g.image * g.image, a.image)

        # test for shape
        g = a.gamma('srgb')
        self.assertEqual(g.shape, a.shape)

        a = Image(np.random.rand(5, 5))
        g = a.gamma(0.5)
        nt.assert_array_almost_equal(g.shape, a.shape)
        nt.assert_array_almost_equal(g.gamma(2).image, a.image)

        a = Image(np.random.rand(5, 5, 3))
        g = a.gamma(0.5)
        nt.assert_array_almost_equal(g.shape, a.shape)

    def test_spectrumfunctions(self):
        r = color.rluminos(555e-9)  # just checks if the code runs

        lam = np.arange(400, 705, 5) * 1e-9
        r = color.rluminos(lam)

        self.assertAlmostEqual(np.max(r), 1.0, delta=1e-3)
        self.assertAlmostEqual(np.min(r), 0.0, delta=1e-3)


# ---------------------------------------------------------------------------------------#
if __name__ == '__main__':

    unittest.main()

    #import code
    #code.interact(local=dict(globals(), **locals()))
