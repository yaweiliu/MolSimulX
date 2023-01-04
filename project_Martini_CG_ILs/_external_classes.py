import numpy as np

from _external_constants import *
from _external_functions import *

class Mol(object):
    '''molecule'''
    def __init__(self,mol_info,AAdirectory,CGdirectory):
        self.name = mol_info[0]
        self.resname = mol_info[1] # resname in 
        self.molAA = mol_info[2] # one mol from AA mdanalysis uni.
        self.mfile = mol_info[3] # AA2CG mapper file
        self.AAdirectory = AAdirectory
        self.CGdirectory = CGdirectory

        self.natom = None
        self.nbead = None
        self.nbond = 0
        self.nangle = 0
        self.ndihed = 0

        self.beads = []
        self.bonds = []
        self.angles = []
        self.diheds = []
        
        self.mapper()
        self.m,self.q = self.mass_charge()
        print('   ',self.__str__())

    def __str__(self):
        return 'molecule {}  {:d} beads for  {:d} atoms  m = {:.4f}  q = {:.4f}'.format(self.name,
            self.nbead, self.natom, self.m, self.q)
            
    def mass_charge(self):
        '''calculate molecule mass and charge from beads'''
        q = 0.0; m = 0.0
        for bd in self.beads:
            q += bd.q
            m += bd.m
        return m, q
        
    def mapper(self):
        '''read AA2CG mapper'''
        print('read CG mapper ...')
        
        f = open(self.mfile, 'r')
        for line in f:
            if line.isspace():continue
            elif '[' in line.split():
                uname = line.split()[1]
            else:   
                atom_indices = list(map(int,line.split()))
                atom_indices.sort()
                atom_indices = list(np.array(atom_indices)-1)
                self.beads.append(Bead(uname,atom_indices))
        f.close()
        self.nbead = len(self.beads)

        # check mapper
        flattened = [val for bd in self.beads for val in bd.atom_indices]
        self.natom = len(flattened)
        res = set([x for x in flattened if flattened.count(x) > 1])
        if len(res)>0: 
            raise ValueError('there are repeated atom index:',res)
        if self.natom != self.molAA.n_atoms:
            raise ValueError('not all atoms in mapper file')

        # bead mass and charge
        print('    id    name    uname    mass      charge    atom_indices')
        for i in range(self.nbead):
            self.beads[i].m = np.sum(self.molAA.atoms.masses[self.beads[i].atom_indices],axis=0)
            self.beads[i].q = np.sum(self.molAA.atoms.charges[self.beads[i].atom_indices],axis=0)

            print('    %2d  %6s   %6s     %.3f    %.3f    ' %(i,self.beads[i].name,self.beads[i].uname,self.beads[i].m,self.beads[i].q), self.beads[i].atom_indices)
            print('                                               ',self.molAA.atoms.elements[self.beads[i].atom_indices])

    def connectivity(self,bonds):
        print('analyse CG connectivity ...')
        for bd in bonds:
            if bd[0]<bd[-1]: bd.reverse()
        bonds.sort(reverse = True)
        
        self.bonds = [Bond(bd[0],bd[1]) for bd in bonds]
        angles,diheds = anglesdiheds(self.bonds,self.nbead)
        self.angles = [Angle(an[0],an[1],an[2]) for an in angles]
        self.diheds = [Dihed(dh[0],dh[1],dh[2],dh[3]) for dh in diheds]
        self.write_BAD()

    def write_BAD(self):
        self.nbond = len(self.bonds)
        self.nangle = len(self.angles)
        self.ndihed = len(self.diheds)
        line = [[bd.i,bd.j] for bd in self.bonds]
        print('    %d bonds:     ' %self.nbond,line)
        line = [[an.i,an.j,an.k] for an in self.angles]
        print('    %d angles:    ' %self.nangle,line)
        line = [[dh.i,dh.j,dh.k,dh.l] for dh in self.diheds]
        print('    %d dihedrals: ' %self.ndihed,line)

    def find_leading_bond(self,i):
        '''find bond with the first atom is i, and i is the largest index'''
        for bd in self.bonds:
            if bd.i == i:
                if bd.i > bd.j: return bd
        return False

    def find_leading_angle(self,i):
        '''find angle with the first atom is i, and i is the largest index'''
        for an in self.angles:
            if an.i == i:
                if an.i > an.j and an.i > an.k: return an
        return False

    def find_leading_dihed(self,i):
        '''find dihedral with the first atom is i, and i is the largest index'''
        for dh in self.diheds:
            if dh.i == i:
                if dh.i > dh.j and dh.i > dh.k and dh.i > dh.l: return dh
        return False

    def find_bond(self,i,j):
        '''find bond for i-j'''
        for bd in self.bonds:
            if bd.i == i and bd.j == j:
                return bd
        return False
    
    def find_angle(self,i,j,k):
        '''find angle for i-j-k'''
        for an in self.angles:
            if an.i == i and an.j == j and an.k == k:
                return an
        return False
    
    def write_zmat_ff(self):
        print('write .zmat and .ff files for %s ...' %self.name)
        filename = self.AAdirectory+'./%s_CG.zmat' %self.name
        f = open(filename, 'w')
        f.write('%s_CG\n'%self.name)
        f.write('\n')

        bond_indices = [] # not additional bond
        for i in range(self.nbead):
            leading_bd = self.find_leading_bond(i)
            leading_an = self.find_leading_angle(i)
            leading_dh = self.find_leading_dihed(i)
            if leading_dh:
                dh = leading_dh
                an = self.find_angle(dh.i,dh.j,dh.k)
                bd = self.find_bond(dh.i,dh.j)
                bond_indices.append(self.bonds.index(bd))
                # id name id bond id angle id dihedral
                f.write('%3d  %6s  %3d  %12.6f  %3d  % 12.6f  %d  % 12.6f\n' %(i+1,
                        self.beads[i].uname,dh.j+1,bd.r,dh.k+1,an.theta,dh.l+1,dh.phi))
            elif leading_an :
                an = leading_an
                bd = self.find_bond(an.i,an.j)
                bond_indices.append(self.bonds.index(bd))
                # id name id bond id angle
                f.write('%3d  %6s  %3d  %12.6f  %3d  % 12.6f\n' %(i+1,
                        self.beads[i].uname,an.j+1,bd.r,an.k+1,an.theta))
            elif leading_bd :
                bd = leading_bd
                bond_indices.append(self.bonds.index(bd))
                # id name id bond
                f.write('%3d  %6s  %3d  %12.6f\n' %(i+1,
                        self.beads[i].uname,bd.j+1,bd.r))
            else:
                f.write('%3d  %6s\n' %(i+1,self.beads[i].uname))
        f.write('\n')

        # add more connection info.
        if len(bond_indices) < self.nbond:
            for i in range(self.nbond):
                if i not in bond_indices:
                     f.write('connect %d %d\n'%(self.bonds[i].i+1,self.bonds[i].j+1)) # add connet info.
        f.write('\n')
        
        # add force field file
        f.write('%s_CG.ff\n'%self.name)
        f.close()
            

        # force field file
        filename = self.AAdirectory+'./%s_CG.ff' %self.name
        f = open(filename, 'w')
        f.write('# non-bond potential: lj \n')
        f.write('# bond and angle potential: k/2(x-x0)^2 \n')
        f.write('# dihedral potential: opls \n')
        f.write('\n')

        #atoms
        f.write('ATOMS\n')
        f.write('# name    name     mass           charge     pot  sigma(A)   epsilon(kJ/mol)\n')
        for bead in self.beads:
            #name name mass charge lj sigma epsilon
            f.write('%6s  %6s  %12.6f  % 12.6f   %2s   0.00   0.00\n'
                    %(bead.uname,bead.uname,bead.m,bead.q,'lj'))
        f.write('\n')

        #bonds
        f.write('BONDS\n')
        f.write('# name    name    pot       x0(A)         k(kJ/mol/A-2)\n')
        for bd in self.bonds:
            # name name pot x0 k
            f.write('%6s  %6s  %6s  % 12.6f   %6d\n'
                    %(self.beads[bd.i].uname,self.beads[bd.j].uname,
                    bd.pot,bd.par[0],bd.par[1])) 
        f.write('\n')

        #angles
        f.write('ANGLES\n')
        f.write('# name    name    name    pot     x0(deg)        k(kJ/mol/rad-2)\n')
        for an in self.angles:
            # name name name harm x0 k
            f.write('%6s  %6s  %6s  %6s  % 12.6f   %6d\n'
                    %(self.beads[an.i].uname,self.beads[an.j].uname,self.beads[an.k].uname,
                    an.pot,an.par[0],an.par[1]))
        f.write('\n')

        #diherals
        f.write('DIHEDRALS\n')
        f.write('# name    name    name    name    pot      k1(KJ/mol)     k2(KJ/mol)     k3(KJ/mol)     k4(KJ/mol)\n')
        for dh in self.diheds:
            # name name name name opls k1 k2 k3 k4
            f.write('%6s  %6s  %6s  %6s  %6s  % 12.6f   % 12.6f   % 12.6f   % 12.6f\n'
                    %(self.beads[dh.i].uname,self.beads[dh.j].uname,self.beads[dh.k].uname,self.beads[dh.l].uname,
                    dh.pot,dh.par[0],dh.par[1],dh.par[2],dh.par[3]))
        f.write('\n')

        f.close()

class Bead(object):
    '''martini beads'''
    def __init__(self,name,atom_indices):
        self.uname = name # unique name
        self.name = bead_symbol(name)
        self.m = 0.0
        self.q = 0.0
        self.atom_indices = atom_indices

class Bond(object):
    '''covalent bond in a molecule'''
    def __init__(self, i=-1, j=-1, r=0.0):
        self.i = i
        self.j = j
        self.r = r
        self.ityp = -1
        self.distribution_AA = None
        self.distribution_CG = None
       
    def __str__(self):
        if hasattr(self, 'name'):
            if self.i != -1:
                return 'bond {:4d} {:4d}  {}  {} {}'.format(self.i,
                    self.j, self.name, self.pot, str(self.par))
            else:
                return 'bond {}  {} {}'.format(self.name, self.pot,
                    str(self.par))
        else:
            return 'bond {:4d} {:4d}'.format(self.i, self.j)

    def setpar(self, iatp, jatp, pot, par):
        '''set bond parameters'''
        self.name = '{}-{}'.format(iatp, jatp)
        self.iatp = iatp
        self.jatp = jatp
        self.pot = pot
        self.par = par

    def seteqval(self):
        '''set bond equilibrium length'''
        if not hasattr(self, 'name'):
            raise RuntimeError('bond parameters not set')
        if self.pot == 'harm':
            self.eqval = self.par[0]
        elif self.pot == 'cons':
            self.eqval = self.par[0]
        else:
            raise ValueError('unkown bond potential ' + self.pot)

class Angle(object):
    '''valence angle'''
    def __init__(self, i=-1, j=-1, k=-1, theta=0.0):
        self.i = i
        self.j = j
        self.k = k
        self.theta = theta
        self.ityp = -1
        self.distribution_AA = None
        self.distribution_CG = None

    def __str__(self):
        if hasattr(self, 'name'):
            if self.i != -1:
                return 'angle {:4d} {:4d} {:4d}  {}  {} {}'.format(
                    self.i, self.j, self.k,
                    self.name, self.pot, str(self.par))
            else:
                return 'angle {}  {} {}'.format(self.name, self.pot,
                                                str(self.par))
        else:
            return 'angle {:4d} {:4d} {:4d}'.format(self.i, self.j,
                                                    self.k)
    
    def setpar(self, iatp, jatp, katp, pot, par):
        '''set angle parameters'''
        self.name = '{0}-{1}-{2}'.format(iatp, jatp, katp)
        self.iatp = iatp
        self.jatp = jatp
        self.katp = katp
        self.pot = pot
        self.par = par

    def seteqval(self):
        '''set angle equilibrium value'''
        if not hasattr(self, 'name'):
            raise RuntimeError('angle parameters not set')
        if self.pot == 'harm':
            self.eqval = self.par[0]
        elif self.pot == 'cons':
            self.eqval = self.par[0]
        else:
            raise ValueError('unkown angle potential ' + self.pot)

class Dihed(object):
    '''dihedral angle (torsion)'''
    def __init__(self, i=-1, j=-1, k=-1, l=-1, phi=0.0):
        self.i = i
        self.j = j
        self.k = k
        self.l = l
        self.phi = phi
        self.ityp = -1
        self.distribution_AA = None
        self.distribution_CG = None

    def __str__(self):
        if hasattr(self, 'name'):
            if self.i != -1:
                return 'dihedral {:4d} {:4d} {:4d} {:4d}  {}  {} {:.1f} {}'.format(
                    self.i, self.j, self.k, self.l,
                    self.name, self.pot, self.phi, str(self.par))
            else:
                return 'dihedral {}  {} {:.1f} {}'.format(self.name, self.pot, self.phi,
                                                str(self.par))
        else:
            return 'dihedral {:4d} {:4d} {:4d} {:4d}'.format(self.i,
                    self.j, self.k, self.l)
    
    def setpar(self, iatp, jatp, katp, latp, pot, par):
        '''set dihedral parameters'''
        self.name = '{}-{}-{}-{}'.format(iatp, jatp, katp, latp)
        self.iatp = iatp
        self.jatp = jatp
        self.katp = katp
        self.latp = latp
        self.pot = pot
        self.par = par