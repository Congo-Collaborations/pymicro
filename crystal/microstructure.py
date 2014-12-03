'''
The microstructure module provide elementary classes to describe a 
crystallographic granular microstructure such as mostly present in 
metallic materials.
'''
import numpy as np
import os, vtk
from matplotlib import pyplot as plt, colors, cm
from xml.dom.minidom import Document, parse

class Orientation:
  '''
  Crystallographic orientation class.
  this follows the passive rotation definition which means that it brings 
  the sample coordinate system into coincidence with the crystal coordinate 
  system. Then one may express a vector Vc in the crystal coordinate system 
  from the vector in the sample coordinate system Vs by:
  
  Vc = B.Vs
  
  and inversely (because B^-1=B^T):
  
  Vs = B^T.Vc
  '''

  def __init__(self, matrix):
    '''Initialization from the 9 components of the orientation matrix.'''
    g = np.array(matrix, dtype=np.float64).reshape((3, 3))
    self._matrix = g
    self.euler = Orientation.OrientationMatrix2Euler(g)
    self.rod = Orientation.OrientationMatrix2Rodrigues(g)

  def orientation_matrix(self):
    return self._matrix

  def __repr__(self):
    '''Provide a string representation of the class.'''
    s = 'Crystal Orientation'
    s += '\norientation matrix = %s' % self._matrix.view()
    s += '\nEuler angles (degrees) = (%8.3f,%8.3f,%8.3f)' % (self.phi1(), self.Phi(), self.phi2())
    s += '\nRodrigues vector = %s' % self.OrientationMatrix2Rodrigues(self._matrix)
    return s

  def phi1(self):
    '''Convenience methode to expose the first Euler angle.'''
    return self.euler[0]

  def Phi(self):
    '''Convenience methode to expose the second Euler angle.'''
    return self.euler[1]

  def phi2(self):
    '''Convenience methode to expose the third Euler angle.'''
    return self.euler[2]

  def to_xml(self, doc):
    '''
    Returns an XML representation of the Orientation instance.
    '''
    orientation = doc.createElement('Orientation')
    orientation_phi1 = doc.createElement('phi1')
    orientation_phi1_text = doc.createTextNode('%f' % self.phi1())
    orientation_phi1.appendChild(orientation_phi1_text)
    orientation.appendChild(orientation_phi1)
    orientation_Phi = doc.createElement('Phi')
    orientation_Phi_text = doc.createTextNode('%f' % self.Phi())
    orientation_Phi.appendChild(orientation_Phi_text)
    orientation.appendChild(orientation_Phi)
    orientation_phi2 = doc.createElement('phi2')
    orientation_phi2_text = doc.createTextNode('%f' % self.phi2())
    orientation_phi2.appendChild(orientation_phi2_text)
    orientation.appendChild(orientation_phi2)
    return orientation

  @staticmethod
  def from_xml(orientation_node):
    orientation_phi1 = orientation_node.childNodes[0]
    orientation_Phi = orientation_node.childNodes[1]
    orientation_phi2 = orientation_node.childNodes[2]
    phi1 = float(orientation_phi1.childNodes[0].nodeValue)
    Phi = float(orientation_Phi.childNodes[0].nodeValue)
    phi2 = float(orientation_phi2.childNodes[0].nodeValue)
    orientation = Orientation.from_euler(np.array([phi1, Phi, phi2]))
    return orientation

  @staticmethod
  def from_euler(euler):
    g = Orientation.Euler2OrientationMatrix(euler)
    o = Orientation(g)
    return o

  @staticmethod
  def from_rodrigues(rod):
    g = Orientation.Rodrigues2OrientationMatrix(rod)
    o = Orientation(g)
    return o

  @staticmethod
  def Euler2OrientationMatrix(euler):
    '''
    Compute the orientation matrix associated with the 3 Euler angles 
    (given in degrees).
    '''
    (rphi1, rPhi, rphi2) = np.radians(euler)
    c1 = np.cos(rphi1)
    s1 = np.sin(rphi1)
    c = np.cos(rPhi)
    s = np.sin(rPhi)
    c2 = np.cos(rphi2)
    s2 = np.sin(rphi2)

    # rotation matrix B
    b11 = c1*c2 - s1*s2*c
    b12 = s1*c2 + c1*s2*c
    b13 = s2*s
    b21 = -c1*s2 - s1*c2*c
    b22 = -s1*s2 + c1*c2*c
    b23 = c2*s
    b31 = s1*s
    b32 = -c1*s
    b33 = c
    B = np.array([[b11, b12, b13], [b21, b22, b23], [b31, b32, b33]])
    return B

  @staticmethod
  def OrientationMatrix2Euler(g, eps=0.000001):
    '''
    Compute the Euler angles (in degrees) from the orientation matrix.
    '''
    # compute rodrigues vector
    R = Orientation.OrientationMatrix2Rodrigues(g, eps=eps)
    if np.abs(g[2,2] - 1) < eps:
      phi1 = 0.5*np.arctan(g[0,1] / g[0,0])
      Phi = 0.0
      phi2 = phi1
    else:
      phi1 = np.arctan(-g[2,0] / g[2,1])
      Phi = np.arccos(g[2,2])
      phi2 = np.arctan(g[0,2] / g[1,2])
    # conditions determined by Jia Li, fev 2012
    if phi1 < 0:
      if phi2 > 0:
        if R[0] > 0:
          phi1 += 2*np.pi
        else:
          phi1 += np.pi
          phi2 += np.pi
      else: # phi2 < 0
        if R[0] > 0:
          phi1 += 2*np.pi
          phi2 += 2*np.pi
        else:
          phi1 += np.pi
          phi2 += np.pi
    else: # phi1 > 0
      if phi2 > 0:
        if R[0] > 0:
          pass # nothing special here
        else:
          phi1 += np.pi
          phi2 += np.pi
      else: # phi2 < 0
        if R[0] > 0:
          pass # nothing special here
        else:
          phi1 += np.pi
          phi2 += np.pi        
    return np.degrees(np.array([phi1, Phi, phi2]))

  @staticmethod
  def OrientationMatrix2Rodrigues(g, eps=0.000001):
    '''
    Compute the rodrigues vector from the orientation matrix.
    '''
    t = g.trace() + 1
    if np.abs(t) < eps:
      return np.zeros(3)
    else:
      r1 = (g[1,2] - g[2,1]) / t
      r2 = (g[2,0] - g[0,2]) / t
      r3 = (g[0,1] - g[1,0]) / t
    return np.array([r1, r2, r3])

  @staticmethod
  def Rodrigues2OrientationMatrix(rod, eps=0.000001):
    '''
    Compute the orientation matrix from the rodrigues vector.
    '''
    r = np.linalg.norm(rod)
    I = np.diagflat(np.ones(3))
    if r < eps:
      return I
    else:
      theta = 2*np.arctan(r)
      n = rod / r
      omega = np.array([[0.0, n[2], -n[1]], [-n[2], 0.0, n[0]], [n[1], -n[0], 0.0]])
      return I + np.sin(theta) * omega + (1 - np.cos(theta)) * omega.dot(omega)

  @staticmethod
  def Euler2Quaternion(euler):
    '''
    Compute the quaternion from the 3 euler angles (in degrees)
    '''
    (phi1, Phi, phi2) = np.radians(euler)
    q0 = np.cos(0.5 * (phi1 + phi2)) * np.cos(0.5*Phi)
    q1 = np.cos(0.5 * (phi1 - phi2)) * np.sin(0.5*Phi)
    q2 = np.sin(0.5 * (phi1 - phi2)) * np.sin(0.5*Phi)
    q3 = np.sin(0.5 * (phi1 + phi2)) * np.cos(0.5*Phi)
    return np.array([q0, q1, q2, q3])

  @staticmethod
  def Euler2Rodrigues(euler):
    '''
    Compute the rodrigues vector from the 3 euler angles (in degrees)
    '''
    (phi1, Phi, phi2) = np.radians(euler)
    a = 0.5 * (phi1 - phi2)
    b = 0.5 * (phi1 + phi2)
    r1 = np.tan(0.5*Phi) * np.cos(a) / np.cos(b)
    r2 = np.tan(0.5*Phi) * np.sin(a) / np.cos(b)
    r3 = np.tan(b)
    return np.array([r1, r2, r3])
    
  @staticmethod
  def read_euler_from_zset_inp(inp_path):
    '''
    Read a set of grain orientations from a z-set input file.
    '''
    inp = open(inp_path)
    lines = inp.readlines()
    for i,line in enumerate(lines):  
      if line.lstrip().startswith('***material'):
        break
    euler_lines = []
    for j,line in enumerate(lines[i+1:]):  
      if line.lstrip().startswith('***'):
        break
      if (not line.lstrip().startswith('%') and line.find('**elset')>0):
        euler_lines.append(line)
    euler = []
    for l in euler_lines:
      tokens = l.split()
      elset = tokens[tokens.index('**elset')+1]
      phi1 = tokens[tokens.index('*rotation')+1]
      Phi = tokens[tokens.index('*rotation')+2]
      phi2 = tokens[tokens.index('*rotation')+3]
      angles = np.array([float(phi1), float(Phi), float(phi2)])
      euler.append([elset, Orientation.from_euler(angles)])
    return dict(euler)

class Grain:
  '''
  Class defining a crystallographic grain.

  A grain has its own crystallographic orientation.
  An optional id for the grain may be specified.
  The position field is the center of mass of the grain in world coordinates.
  The volume of the grain is expressed in pixel/voxel unit.
  '''

  def __init__(self, grain_id, grain_orientation):
    self.id = grain_id
    self.orientation = grain_orientation
    self.position = (0, 0, 0)
    self.volume = 0
    self.vtkmesh = None
    #self.records = []

  def __repr__(self):
    '''Provide a string representation of the class.'''
    s = '%s\n * id = %d\n' % (self.__class__.__name__, self.id)
    s += ' * %s\n' % (self.orientation)
    s += ' * position (%f, %f, %f)\n' % (self.position)
    s += ' * has vtk mesh ? %s\n' % (self.vtkmesh != None)
    return s
    
  def schmid_factor(self, slip_system, load_direction=[0., 0., 1]):
    plane = slip_system.get_slip_plane()
    Bt = self.orientation_matrix().transpose()
    n_rot = np.dot(Bt, plane.normal()) # plane.normal() is a unit vector
    slip = slip_system.get_slip_direction().direction()
    slip_rot = np.dot(Bt, slip)
    SF = np.abs(np.dot(n_rot, load_direction) * np.dot(slip_rot, load_direction))
    return SF

  def SetVtkMesh(self, mesh):
    self.vtkmesh = mesh
    
  def add_vtk_mesh(self, array, contour=True, verbose=False):
    label = self.id # we use the grain id here... 
    # create vtk structure
    from scipy import ndimage
    from vtk.util import numpy_support
    grain_size = np.shape(array)
    array_bin = (array == label).astype(np.uint8)
    if verbose: print np.unique(array_bin)
    local_com = ndimage.measurements.center_of_mass(array_bin, array)
    vtk_data_array = numpy_support.numpy_to_vtk(np.ravel(array_bin, order='F'), deep=1)
    grid = vtk.vtkUniformGrid()
    grid.SetOrigin(-local_com[0], -local_com[1], -local_com[2])
    grid.SetSpacing(1, 1, 1)
    grid.SetScalarType(vtk.VTK_UNSIGNED_CHAR)
    if contour:
      grid.SetExtent(0, grain_size[0]-1, 0, grain_size[1]-1, 0, grain_size[2]-1)
      grid.GetPointData().SetScalars(vtk_data_array)
      # contouring selected grain
      contour = vtk.vtkContourFilter()
      contour.SetInput(grid)
      contour.SetValue(0, 0.5)
      contour.Update()
      if verbose: print contour.GetOutput()
      self.SetVtkMesh(contour.GetOutput())
    else:
      grid.SetExtent(0, grain_size[0], 0, grain_size[1], 0, grain_size[2])
      grid.GetCellData().SetScalars(vtk_data_array)
      # threshold selected grain
      if verbose: print 'thresholding label', label
      thresh = vtk.vtkThreshold()
      thresh.ThresholdBetween(0.5, 1.5)
      #thresh.ThresholdBetween(label-0.5, label+0.5)
      thresh.SetInput(grid)
      thresh.Update()
      if verbose: print thresh.GetOutput()
      self.SetVtkMesh(thresh.GetOutput())

  def to_xml(self, doc, file_name=None):
    '''
    Returns an XML representation of the Grain instance.
    '''
    grain = doc.createElement('Grain')
    grain_id = doc.createElement('Id')
    grain_id_text = doc.createTextNode('%s' % self.id)
    grain_id.appendChild(grain_id_text)
    grain.appendChild(grain_id)
    grain.appendChild(self.orientation.to_xml(doc))
    grain_position = doc.createElement('Position')
    grain_position_x = doc.createElement('X')
    grain_position.appendChild(grain_position_x)
    grain_position_x_text = doc.createTextNode('%f' % self.position[0])
    grain_position_x.appendChild(grain_position_x_text)
    grain_position_y = doc.createElement('Y')
    grain_position.appendChild(grain_position_y)
    grain_position_y_text = doc.createTextNode('%f' % self.position[1])
    grain_position_y.appendChild(grain_position_y_text)
    grain_position_z = doc.createElement('Z')
    grain_position.appendChild(grain_position_z)
    grain_position_z_text = doc.createTextNode('%f' % self.position[2])
    grain_position_z.appendChild(grain_position_z_text)
    grain.appendChild(grain_position)
    grain_mesh = doc.createElement('Mesh')
    if not file_name:
      file_name = self.vtk_file_name()
    grain_mesh_text = doc.createTextNode('%s' % file_name)
    grain_mesh.appendChild(grain_mesh_text)
    grain.appendChild(grain_mesh)
    return grain

  @staticmethod
  def from_xml(grain_node):
    grain_id = grain_node.childNodes[0]
    grain_orientation = grain_node.childNodes[1]
    orientation = Orientation.from_xml(grain_orientation)
    id = int(grain_id.childNodes[0].nodeValue)
    grain = Grain(id, orientation)
    grain_position = grain_node.childNodes[2]
    xg = float(grain_position.childNodes[0].childNodes[0].nodeValue)
    yg = float(grain_position.childNodes[1].childNodes[0].nodeValue)
    zg = float(grain_position.childNodes[2].childNodes[0].nodeValue)
    grain.position = (xg, yg, zg)
    grain_mesh = grain_node.childNodes[3]
    grain_mesh_file = grain_mesh.childNodes[0].nodeValue
    print grain_mesh_file
    grain.load_vtk_repr(grain_mesh_file)
    return grain
    
  def vtk_file_name(self):
    return 'grain_%d.vtu' % self.id
    
  def save_vtk_repr(self, file_name=None):
    import vtk
    if not file_name:
      file_name = self.vtk_file_name()
    print 'writting ' + file_name
    writer = vtk.vtkXMLUnstructuredGridWriter()
    writer.SetFileName(file_name)
    writer.SetInput(self.vtkmesh)
    writer.Write()

  def load_vtk_repr(self, file_name):
    import vtk
    print 'reading ' + file_name
    reader = vtk.vtkXMLUnstructuredGridReader()
    reader.SetFileName(file_name)
    reader.Update()
    self.vtkmesh = reader.GetOutput()

  def orientation_matrix(self):
    '''Returns the grain orientation matrix.'''
    return self.orientation.orientation_matrix()

  def dct_omega_angles(self, hkl, lambda_keV, verbose=True):
    '''Compute the two omega angles which satisfy the Bragg condition.
    
    According to the Bragg's law, a crystallographic grain will be in 
    diffracting condition if:
    
    .. math::
    
       \sin\\theta=-[\Omega g^{-1}h]_1
       
    This method solves the associated second order equation to return 
    the two corresponding omega angles.
    
    .. warning::
    
       Cubic lattice is assumed which turn the matrix S into the identity.
       
    '''
    (h, k, l) = hkl.miller_indices()
    (a, b, c) = hkl._lattice._lengths
    theta = hkl.bragg_angle(lambda_keV, verbose=verbose)
    lambda_nm = 1.2398 / lambda_keV

    Bt = self.orientation_matrix().transpose()
    A = h*Bt[0,0] + k*Bt[1,0] + l*Bt[2,0]
    B = -h*Bt[0,1] - k*Bt[1,1] - l*Bt[2,1]
    C = 2*a*np.sin(theta)**2 / lambda_nm
    Delta = 4*(A**2 + B**2 - C**2)
    if Delta < 0:
      raise ValueError('Delta < 0')
    if verbose:
      print 'A=',A
      print 'B=',B
      print 'C=',C
      print 'Delta=',Delta
    t1 = (B - 0.5 * np.sqrt(Delta)) / (A+C)
    t2 = (B + 0.5 * np.sqrt(Delta)) / (A+C)
    w1 = 2 * np.arctan(t1) * 180. / np.pi
    w2 = 2 * np.arctan(t2) * 180. / np.pi
    if verbose:
      print 't1=%.3f and t2=%.3f' % (t1, t2)
      print 'w1=%.3f and w2=%.3f' % (w1, w2)
      print 'verifying Acos(w)+Bsin(w)=C:'
      for t in (t1,t2):
        print A*(1-t**2)/(1+t**2)+B*2*t/(1+t**2)
      print 'verifying (A+C)*t**2-2*B*t+(C-A)=0'
      for t in (t1,t2):
        print (A+C)*t**2-2*B*t+(C-A)
    return (w1, w2)
    
class Microstructure:
  '''
  Class used to manipulate a full microstructure.
  
  It is typically defined as a list of grains objects.
  '''
  def __init__(self, name='empty'):
    self.name = name
    self.grains = []
    self.vtkmesh = None

  @staticmethod
  def rand_cmap(N=4096, first_is_black = False):
    '''Creates a random color map.
    
       The first color can be enforced to black and usually figure out the background.
       The random seed is fixed to consistently produce the same colormap.
    '''
    np.random.seed(13)
    rand_colors = np.random.rand(N, 3)
    if first_is_black:
      rand_colors[0] = [0., 0., 0.] # enforce black background (value 0)
    return colors.ListedColormap(rand_colors)
    
  @staticmethod
  def from_xml(xml_file_name, grain_ids=None):
    '''Load a Microstructure object from an xml file.
    
    It is possible to restrict the grains which are loaded by providing 
    the list of ids of the grains of interest.
    '''
    print grain_ids
    micro = Microstructure()
    dom = parse(xml_file_name)
    root = dom.childNodes[0]
    name = root.childNodes[0]
    micro.name = name.childNodes[0].nodeValue
    grains = root.childNodes[1]
    for node in grains.childNodes:
      if grain_ids and not (int(node.childNodes[0].childNodes[0].nodeValue) in grain_ids): continue
      print node
      micro.grains.append(Grain.from_xml(node))
    return micro
    
  def get_grain(self, gid):
    '''Get a particular grain given its id.
    
    This method browses the microstructure and return the grain 
    corresponding to the given id. If the grain is not found, the 
    method raises a `ValueError`.

    *Parameters*

    **gid**: the grain id.
    
    *Returns*

    The method return a `Grain` with the corresponding id.
    '''
    for grain in self.grains:
      if grain.id == gid:
        return grain
    raise ValueError('grain %d not found in the microstructure' % gid)

  def __repr__(self):
    '''Provide a string representation of the class.'''
    s = '%s\n' % self.__class__.__name__
    s += '* name: %s\n' % self.name
    for g in self.grains:
      s += '* %s' % g.__repr__
    return s
  
  def SetVtkMesh(self, mesh):
    self.vtkmesh = mesh

  def to_xml(self, doc):
    '''
    Returns an XML representation of the Microstructure instance.
    '''
    root = doc.createElement('Microstructure')
    doc.appendChild(root)
    name = doc.createElement('Name')
    root.appendChild(name)
    name_text = doc.createTextNode(self.name)
    name.appendChild(name_text)
    grains = doc.createElement('Grains')
    root.appendChild(grains)
    for i, grain in enumerate(self.grains):
      file_name = os.path.join(self.name, '%s_%d.vtu' % (self.name, i))
      grains.appendChild(grain.to_xml(doc, file_name))

  def save(self):
    '''Saving the microstructure to the disk.
    
    Save the metadata as a XML file and when available, also save the 
    vtk representation of the grains.
    '''
    # save the microstructure instance as xml
    doc = Document()
    self.to_xml(doc)
    xml_file_name = '%s.xml' % self.name
    print 'writting ' + xml_file_name
    f = open(xml_file_name, 'wb')
    doc.writexml(f, encoding= 'utf-8')
    f.close()
    # now save the vtk representation
    if self.vtkmesh != None:
      import vtk
      vtk_file_name = '%s.vtm' % self.name
      print 'writting ' + vtk_file_name
      writer = vtk.vtkXMLMultiBlockDataWriter()
      writer.SetFileName(vtk_file_name)
      writer.SetInput(self.vtkmesh)
      writer.Write()    
    
class EbsdMicrostructure:
  '''
  Class used to manipulate a full microstructure read from an EBSD 
  measurement for instance.
  '''

  def __init__(self, name='empty'):
    self.name = name
    self.type = None
    self.shape = None
    self.records = None

  # this should produce a single array from which you can plot the usual 
  # EBSD stuff. Then add another method which extract a grain list given
  # a criterion (can be grain ID or misorientation)
  def read_from_ebsd(self, filename, grid='square'):
    if (grid != 'square' and grid != 'hex'):
      raise TypeError('unsupported grid type', grid)
    self.name = filename.split('/')[-1]
    self.records = np.loadtxt(filename, usecols=range(9))
    # guess the grid size
    size_x = sum(self.records[:,4] == self.records[0,4])
    size_y = len(self.records[:,4])/size_x
    print 'size is ',size_x, size_y
    self.shape = (size_y,size_x)
    
  def extract_grains(self):
    grain_id_list = np.unique(self.records[:,8]).tolist()
    grain_record_list = np.empty(len(grain_id_list))
    # todo: filter out all records to build array for each grain...
    for record in a:
      # add this line to the corresponding grain_record
      grain_record_list[grain_id_list.index(record[8])].append(record)
    #for record_list in grain_record_list:
    # create a new grain

  # plot the ebsd data using pyplot. have a look at enum to handle all possibilities
  def plot(self, type='Euler', save=False, display=True):
    if type == 'phi1':
      phi1 = self.records[:,0].reshape(self.shape)/np.pi*180.
      plt.imshow(phi1, cmap=cm.hsv, interpolation='nearest')
      plt.clim([0,360])
      plt.colorbar()
      print np.min(phi1), np.max(phi1)
    elif type == 'Phi':
      Phi = self.records[:,1].reshape(self.shape)/np.pi*180.
      plt.imshow(Phi, cmap=cm.hsv, interpolation='nearest')
      plt.clim([0,180])
    elif type == 'phi2':
      phi2 = self.records[:,2].reshape(self.shape)/np.pi*180.
      plt.imshow(phi2, cmap=cm.hsv, interpolation='nearest')
      plt.clim([0,360])
    elif type == 'Euler':
      # provide a MxNx3 array to imshow
      rgb = np.empty((self.shape[0],self.shape[1],3), dtype=float)
      rgb[:,:,0] = self.records[:,0].reshape(self.shape)/(2*np.pi)
      rgb[:,:,1] = self.records[:,1].reshape(self.shape)/(np.pi)
      rgb[:,:,2] = self.records[:,2].reshape(self.shape)/(2*np.pi)
      plt.imshow(rgb, interpolation='nearest')
    elif type == 'IQ':
      iq = self.records[:,5].reshape(self.shape)
      plt.imshow(iq, cmap=cm.gray, interpolation='nearest')
    elif type == 'GID':
      gid = self.records[:,8].reshape(self.shape)
      plt.imshow(gid, cmap=Microstructure.rand_cmap(), interpolation='nearest')
    else:
      raise TypeError('unsupported ebsd plot type', type)
    if save:
      plt.imsave(name + '_' + type + '.png', format='png')
    if display:
      plt.show()
    
if __name__ == '__main__':
  import os
  data_dir = '/home/proudhon/python/samples/dct'
  micro = Microstructure.from_xml(os.path.join(data_dir, 'grains_302x302x100_uint8.xml'))
  print micro
  
  '''
  #g6 = Grain(6, 142.845, 31.966, 214.384)
  #print g6.__repr__
  m = EbsdMicrostructure()
  m.read_from_ebsd('/home/proudhon/students/claudio/ebsd/grainfilepointssquare.txt')
  #m.read_from_ebsd('/home/proudhon/data/ebsd/AlMgSi_Reza/80min_80Cr_17mm_export.txt')
  print m.records.shape
  m.plot(type='GID')
  '''
  print 'done'
