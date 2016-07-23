import unittest
import numpy as np
from pymicro.crystal.lattice import Lattice, HklDirection, HklPlane, SlipSystem

class LatticeTests(unittest.TestCase):

  def setUp(self):
    print 'testing the Lattice class'

  def test_cubic(self):
    a = np.array([[ 0.5,  0. ,  0. ],
                  [ 0. ,  0.5,  0. ],
                  [ 0. ,  0. ,  0.5]])
    l = Lattice.cubic(0.5)
    for i in range(0, 3):
      for j in range(0, 3):
        self.assertEqual(l.matrix[i][j], a[i][j])

  def test_volume(self):
    l = Lattice.cubic(0.5)
    self.assertAlmostEqual(l.volume(), 0.125)
  
  def test_from_symbol(self):
    al = Lattice.from_symbol('Al')
    for i in range(0, 3):
      self.assertAlmostEqual(al._lengths[i], 0.40495)
      self.assertEqual(al._angles[i], 90.0)
  
  def test_reciprocal_lattice(self):
    Mg2Si = Lattice.from_parameters(1.534, 0.405, 0.683, 90., 106., 90.)
    [astar, bstar, cstar] = Mg2Si.reciprocal_lattice()
    self.assertAlmostEqual(astar[0], 0.678, 3)
    self.assertAlmostEqual(astar[1], 0., 3)
    self.assertAlmostEqual(astar[2], 0., 3)
    self.assertAlmostEqual(bstar[0], 0., 3)
    self.assertAlmostEqual(bstar[1], 2.469, 3)
    self.assertAlmostEqual(bstar[2], 0., 3)
    self.assertAlmostEqual(cstar[0], 0.420, 3)
    self.assertAlmostEqual(cstar[1], 0., 3)
    self.assertAlmostEqual(cstar[2], 1.464, 3)

class HklDirectionTests(unittest.TestCase):

  def setUp(self):
    print 'testing the HklDirection class'

  def test_angle_between_directions(self):
    d111 = HklDirection(1, 1, 1)
    d110 = HklDirection(1, 1, 0)
    d100 = HklDirection(1, 0, 0)
    dm111 = HklDirection(-1, 1, 1)
    self.assertAlmostEqual(d100.angle_with_direction(d110)*180/np.pi, 45.0)
    self.assertAlmostEqual(d111.angle_with_direction(d110)*180/np.pi, 35.26, 2)
    self.assertAlmostEqual(d111.angle_with_direction(dm111)*180/np.pi, 70.528, 2)

  def test_tetragonal_direction(self):
    bct = Lattice.body_centered_tetragonal(0.28, 0.40)
    d111 = HklDirection(1, 1, 1, bct)
    d110 = HklDirection(1, 1, 0, bct)
    self.assertAlmostEqual(d111.direction()[0], 0.49746834, 5)
    self.assertAlmostEqual(d111.direction()[1], 0.49746834, 5)
    self.assertAlmostEqual(d111.direction()[2], 0.71066905, 5)
    self.assertAlmostEqual(d110.direction()[0], 0.707106781, 5)
    self.assertAlmostEqual(d110.direction()[1], 0.707106781, 5)
    self.assertAlmostEqual(d110.direction()[2], 0.0, 5)

  def test_tetragonal_direction2(self):
    ZrO2 = Lattice.tetragonal(0.364, 0.527)
    d = HklDirection(1, 1, 1, ZrO2)
    target = np.array([1., 1., 1.448])
    target /= np.linalg.norm(target)
    self.assertAlmostEqual(d.direction()[0], target[0], 4)
    self.assertAlmostEqual(d.direction()[1], target[1], 4)
    self.assertAlmostEqual(d.direction()[2], target[2], 4)

class HklPlaneTests(unittest.TestCase):

  def setUp(self):
    print 'testing the HklPlane class'

  def test_HklPlane(self):
    p = HklPlane(1, 1, 1)
    n = p.normal()
    self.assertEqual(np.linalg.norm(n), 1)
  
  def test_HklPlane_normal(self):
    ZrO2 = Lattice.tetragonal(3.64, 5.27)
    p = HklPlane(1, 1, 1, ZrO2)
    n = p.normal()
    self.assertAlmostEqual(n[0], 0.635, 3)
    self.assertAlmostEqual(n[1], 0.635, 3)
    self.assertAlmostEqual(n[2], 0.439, 3)

  def test_110_normal_monoclinic(self):
    '''This test comes from 
    http://www.mse.mtu.edu/~drjohn/my3200/stereo/sg5.html
    corrected for a few errors in the html page.
    '''  
    Mg2Si = Lattice.from_parameters(1.534, 0.405, 0.683, 90., 106., 90.)
    a = Mg2Si.matrix[0]
    b = Mg2Si.matrix[1]
    c = Mg2Si.matrix[2]
    self.assertAlmostEqual(a[0], 1.475, 3)
    self.assertAlmostEqual(a[1], 0., 3)
    self.assertAlmostEqual(a[2], -0.423, 3)
    self.assertAlmostEqual(b[0], 0., 3)
    self.assertAlmostEqual(b[1], 0.405, 3)
    self.assertAlmostEqual(b[2], 0., 3)
    self.assertAlmostEqual(c[0], 0., 3)
    self.assertAlmostEqual(c[1], 0., 3)
    self.assertAlmostEqual(c[2], 0.683, 3)
    p = HklPlane(1, 1, 1, Mg2Si)
    Gc = p.scattering_vector()
    self.assertAlmostEqual(Gc[0], 1.098, 3)
    self.assertAlmostEqual(Gc[1], 2.469, 3)
    self.assertAlmostEqual(Gc[2], 1.464, 3)
    self.assertAlmostEqual(p.interplanar_spacing(), 0.325, 3)
    Ghkl = np.dot(Mg2Si.matrix, Gc)
    self.assertEqual(Ghkl[0], 1.) # h
    self.assertEqual(Ghkl[1], 1.) # k
    self.assertEqual(Ghkl[2], 1.) # l
    
  def test_scattering_vector(self):
    Fe_fcc = Lattice.face_centered_cubic(0.287) # FCC iron
    hkl = HklPlane(2, 0, 0, Fe_fcc)
    Gc = hkl.scattering_vector()
    self.assertAlmostEqual(np.linalg.norm(Gc), 1/hkl.interplanar_spacing()) 
    Al_fcc = Lattice.face_centered_cubic(0.405)
    hkl = HklPlane(0, 0, 2, lattice = Al_fcc)
    Gc = hkl.scattering_vector()
    self.assertAlmostEqual(np.linalg.norm(Gc), 1/hkl.interplanar_spacing()) 

  def test_bragg_angle(self):
    l = Lattice.cubic(0.287) # FCC iron
    hkl = HklPlane(2, 0, 0, l) # 200 reflection at 8 keV is at 32.7 deg
    self.assertAlmostEqual(hkl.bragg_angle(8), 0.5704164) 

class SlipSystemTests(unittest.TestCase):

  def setUp(self):
    print 'testing the SlipSystem class'

  def test_get_slip_system(self):
    ss = SlipSystem.get_slip_systems('111')
    self.assertEqual(len(ss), 12)
    for s in ss:
      n = s.get_slip_plane().normal()
      l = s.get_slip_direction().direction()
      self.assertEqual(np.dot(n, l), 0.)
    ss = SlipSystem.get_slip_systems('112')
    self.assertEqual(len(ss), 12)
    for s in ss:
      n = s.get_slip_plane().normal()
      l = s.get_slip_direction().direction()
      self.assertEqual(np.dot(n, l), 0.)
    
if __name__ == '__main__':
  unittest.main()
