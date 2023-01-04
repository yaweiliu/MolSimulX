import numpy as np
import re
import MDAnalysis as mda
from MDAnalysis import transformations
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt

def cal_force_coeff(data,kBT,flag,label='AA'):
    N = max(4,int(np.sqrt(len(data))))
    M = int(len(data)/N)
    if M*N<len(data): M += 1
    
    fig = plt.figure(figsize=(3*N,1.5*M), dpi=140);
    ncount = 0
    coeffs = []
    for i in range(len(data)):
        ncount += 1
        ax = fig.add_subplot(int('%d%d%d'%(M,N,ncount)));
        if label == 'AA': centers,count,x0 = data[i].distribution_AA
        else: centers,count,x0 = data[i].distribution_CG

        #for angle/dihedral, plot in degrees
        if flag == 'bond': centers_plot = centers
        else: centers_plot = np.degrees(centers)

        #for dihedral, using opls
        if flag == 'dihedral':
            args = np.where(count==0.)
            mask = np.ones(len(count), dtype=bool)
            mask[args] = False
            centers = centers[mask];count = count[mask]
            centers_plot = np.degrees(centers)
            count = -kBT*np.log(count)
            count -= count[0]
        
        ax.plot(centers_plot,count,'.')

        try:
            if flag == 'bond' or flag == 'angle':
                func = lambda x, A, omega_inv: gaussian(x, A, omega_inv, x0)
                popt,_ = curve_fit(func, centers, count)
                coeffs.append([x0,4*kBT*popt[-1]**2]) #we take k/2(x-x0)^2
            else:
                func = opls
                popt,_ = curve_fit(func, centers, count)
                coeffs.append([x0,popt[0],popt[1],popt[2],popt[3]])
            ax.plot(centers_plot,func(centers,*popt),'r-.',lw=1)
        except RuntimeError:
            ax.plot((x0,x0),(np.min(count),np.max(count)),'r-.',lw=1)
            if flag == 'bond' or flag == 'angle':
                coeffs.append([x0,-9999])
            else:
                coeffs.append([x0,-9999,-9999,-9999,-9999])
            print("Bad fitting! Skip!")

        if flag == 'bond': ax.set_xlabel(r'$x$ [$\AA$]');
        else: ax.set_xlabel(r'$x$ [$^\circ$]');
        
        ax.set_ylabel(r'$p(x)$');
        if flag == 'dihedral': ax.set_ylabel(r'$U(x)$');
        
        ax.tick_params(direction='in')
    
    plt.tight_layout()
    plt.show()

    coeffs = np.array(coeffs)
    if flag == 'angle' or flag == 'dihedral': 
        coeffs[:,0] = np.degrees(coeffs[:,0])

    return coeffs

def compare_BAD(data,flag):
    N = max(4,int(np.sqrt(len(data))))
    M = int(len(data)/N)
    if M*N<len(data): M += 1
    fig = plt.figure(figsize=(3*N,1.5*M), dpi=140);
    ncount = 0
    for i in range(len(data)):
        ncount += 1
        ax = fig.add_subplot(int('%d%d%d'%(M,N,ncount)));
        centers,count,_ = data[i].distribution_AA
        if flag == 'bond': centers_plot = centers
        else: centers_plot = np.degrees(centers)    
        ax.plot(centers_plot,count,'x')

        centers,count,_ = data[i].distribution_CG
        if flag == 'bond': centers_plot = centers
        else: centers_plot = np.degrees(centers)    
        ax.plot(centers_plot,count,'+')
    
        if flag == 'bond': ax.set_xlabel(r'$x$ [$\AA$]');
        else: ax.set_xlabel(r'$x$ [$^\circ$]');
        ax.set_ylabel(r'$p(x)$');
        ax.tick_params(direction='in')   
    plt.tight_layout()
    plt.show()
#---------------------------------------------------------------------------------------------




#---------------------------------------------------------------------------------------------
# main part

class CG_Molecule(object):
    '''CG a molecule'''
    def __init__(self,mol_info,AAdirectory,CGdirectory):
        self.mol_name = mol_info[0]
        self.mol_resid = mol_info[1]
        self.mol_resname = mol_info[2]
        self.mapper_file = mol_info[3]
        self.AAdirectory = AAdirectory
        self.CGdirectory = CGdirectory

        print('CG model for %s ...' %self.mol_name)

    def load_AAtraj(self,AAtraj):
        self.AAtraj = AAtraj

    def load_CGtraj(self,CGtraj):
        self.CGtraj = CGtraj
    
    def mapper(self):
        '''read AA2CG map'''
        print('   Build CG mapper ...')
        filename = self.mapper_file
        openedFile = open(filename, 'r')
        
        self.beads = []
        for line in openedFile:
            if line.isspace():continue
            elif '[' in line.split():
                uname = line.split()[1]
            else:   
                atom_indices = list(map(int,line.split()))
                atom_indices.sort()
                atom_indices = list(np.array(atom_indices)-1)
                self.beads.append(Bead(uname,atom_indices))
        self.bead_num = len(self.beads)

        # check mapper
        flattened = [val for bead in self.beads for val in bead.atom_indices]
        print('      %d CG beads for %d atoms!' %(len(self.beads),len(flattened)))
        res = set([x for x in flattened if flattened.count(x) > 1])
        if len(res)>0: print('   Error: There are repeated atom index:',res)

        # bead mass and charge
        sel = self.AAtraj.select_atoms('resid %d' %self.mol_resid)
        for i in range(self.bead_num):
            self.beads[i].mass = np.sum(sel.atoms.masses[self.beads[i].atom_indices],axis=0)
            self.beads[i].charge = np.sum(sel.atoms.charges[self.beads[i].atom_indices],axis=0)

        print('      #    id   name    uname   mass    charge atom_indices')
        for i in range(self.bead_num):
            print('      bead %2d: %5s   %5s    %.3f  %.3f ' %(i,self.beads[i].name,self.beads[i].uname,self.beads[i].mass,self.beads[i].charge), self.beads[i].atom_indices)
            print('                                              ',sel.atoms.elements[self.beads[i].atom_indices])
    
    def connectivity(self,bonds):
        print('   Analyse CG connectivity ...')
        self.bonds = []
        # sort bonds
        bonds.sort(reverse = True)
        self.bonds = [Bond(bond[0],bond[1]) for bond in bonds]
        self.angles = []
        self.diheds = []
        self.anglesdiheds()
        self.write_bondsanglesdiheds()

    def anglesdiheds(self):
        '''identify angles and dihedrals based on bond connectivity'''
        natom = self.bead_num
        nbond = len(self.bonds)

        # identify valence angles
        for i in range(natom):  # find neighbour atoms to each atom i
            nb = 0
            neib = []
            for bd in self.bonds:          
                if i == bd.i:
                    neib.append(bd.j)
                    nb += 1
                elif i == bd.j:
                    neib.append(bd.i)
                    nb += 1
            for k in range(nb - 1):
                for l in range(k + 1, nb):
                    self.angles.append(Angle(neib[k], i, neib[l]))
        # sort angles
        line = [[an.i,an.j,an.k] for an in self.angles]
        line.sort(reverse = True)
        self.angles = [Angle(an[0],an[1],an[2]) for an in line]

        # identify dihedral angles
        for k in range(nbond): # find bonds around non-terminal bonds
            for l in range(nbond):
                if l == k:
                    continue
                if self.bonds[l].i == self.bonds[k].i:
                    for j in range(nbond):
                        if j == k or j == l:
                            continue
                        if self.bonds[j].i == self.bonds[k].j:
                            self.diheds.append(Dihed(self.bonds[l].j,
                                                    self.bonds[k].i,
                                                    self.bonds[k].j,
                                                    self.bonds[j].j))
                        elif self.bonds[j].j == self.bonds[k].j:
                            self.diheds.append(Dihed(self.bonds[l].j,
                                                    self.bonds[k].i,
                                                    self.bonds[k].j,
                                                    self.bonds[j].i))
                elif self.bonds[l].j == self.bonds[k].i:
                    for j in range(nbond):
                        if j == k or j == l:
                            continue
                        if self.bonds[j].i == self.bonds[k].j:
                            self.diheds.append(Dihed(self.bonds[l].i,
                                                    self.bonds[k].i,
                                                    self.bonds[k].j,
                                                    self.bonds[j].j))
                        elif self.bonds[j].j == self.bonds[k].j:
                            self.diheds.append(Dihed(self.bonds[l].i,
                                                    self.bonds[k].i,
                                                    self.bonds[k].j,
                                                    self.bonds[j].i))

        # sort dihedrals
        line = [[dh.i,dh.j,dh.k,dh.l] for dh in self.diheds]
        line.sort(reverse = True)
        self.diheds = [Dihed(dh[0],dh[1],dh[2],dh[3]) for dh in line]
        
        # remove dihedral with identical atom
        diheds = self.diheds.copy()
        for dh in diheds:
            line = [dh.i,dh.j,dh.k,dh.l]
            if len(set(line)) < len(line):
                self.diheds.remove(dh)

    def write_bondsanglesdiheds(self):
        self.bond_num = len(self.bonds)
        self.angle_num = len(self.angles)
        self.dihed_num = len(self.diheds)
        line = [[bd.i,bd.j] for bd in self.bonds]
        print('      %d bonds:     ' %self.bond_num,line)
        line = [[an.i,an.j,an.k] for an in self.angles]
        print('      %d angles:    ' %self.angle_num,line)
        line = [[dh.i,dh.j,dh.k,dh.l] for dh in self.diheds]
        print('      %d dihedrals: ' %self.dihed_num,line)

    def cal_COGs(self,interval,label='AA'):
        '''compute COGs for each bead from AA/CG simulaiton'''
        if label == 'AA': 
            u = self.AAtraj
            sel = u.select_atoms('resname %s'%self.mol_resname)
            resids = np.unique(sel.atoms.resids)
            allCOGs = []
            for ts in u.trajectory[::interval]:   
                for i in resids:
                    sel = u.select_atoms('resid %d'%i)
                    COGs = []
                    for bead in self.beads:
                        COGs.append(np.mean(sel.atoms.positions[bead.atom_indices],axis=0))
                    allCOGs.append(COGs)
        else:
            u = self.CGtraj
            sel = u.select_atoms('resname %s'%self.mol_resname)
            resids = np.unique(sel.atoms.resids)
            allCOGs = []
            for ts in u.trajectory[::interval]:   
                for i in resids:
                    sel = u.select_atoms('resid %d'%i)
                    allCOGs.append(sel.atoms.positions) # data has sorted
        return allCOGs

    def cal_BADs(self,allCOGs):
        '''calculate BAD for beads'''
        allBonds = []
        allAngles = []
        allDiheds = []
        for i in range(len(allCOGs)):
            bonds = []
            for bd in self.bonds:
                x = cal_bond(allCOGs[i][bd.i],allCOGs[i][bd.j])
                bonds.append(x)
            allBonds.append(bonds)
            
            angles = []
            for an in self.angles:
                x = cal_angle(allCOGs[i][an.i],allCOGs[i][an.j],allCOGs[i][an.k])
                angles.append(x)
            allAngles.append(angles)
            
            diheds = []
            for dh in self.diheds:
                x = cal_dihedral(allCOGs[i][dh.i],allCOGs[i][dh.j],allCOGs[i][dh.k],allCOGs[i][dh.l])
                diheds.append(x)
            allDiheds.append(diheds)
        return [allBonds,allAngles,allDiheds]

    def cal_BAD_distribution(self,allBADs,label='AA'):
        # bond
        if self.bond_num == 0: return
        data = np.array(allBADs[0])
        for i in range(self.bond_num):
            centers,count = histograms(data[:,i])
            x0 = np.mean(data[:,i])
            if label == 'AA': self.bonds[i].distribution_AA = [centers,count,x0]
            else: self.bonds[i].distribution_CG = [centers,count,x0]

        # angle
        if self.angle_num == 0: return
        data = np.array(allBADs[1])
        for i in range(self.angle_num):
            centers,count = histograms(data[:,i])
            x0 = np.mean(data[:,i])
            if label == 'AA': self.angles[i].distribution_AA = [centers,count,x0]
            else: self.angles[i].distribution_CG = [centers,count,x0]

        # dihedral
        if self.dihed_num == 0: return
        data = np.array(allBADs[2])
        for i in range(self.dihed_num):
            centers,count = histograms(data[:,i])
            x0 = np.mean(np.abs(data[:,i])) #take abs value
            if label == 'AA': self.diheds[i].distribution_AA = [centers,count,x0]
            else: self.diheds[i].distribution_CG = [centers,count,x0]
    
    def cal_BAD_from_AA(self,kBT,interval):
        '''calcualte bond, angle, dihedral potentials from the AA simulation'''
        if self.bond_num == 0: return
        print('   Calulcate CG bond, angle and diherdal distribution from AA simulation ...')
        
        allCOGs = self.cal_COGs(interval,label='AA')
        allBADs = self.cal_BADs(allCOGs)
        self.cal_BAD_distribution(allBADs,label='AA')

        print('   Fit bond, angle and diherdal potentials in AA simulation ...')
        if self.bond_num > 0:
            print('      BONDS:')
            coeffs = cal_force_coeff(self.bonds,kBT,flag='bond',label='AA')
            for i,bd in enumerate(self.bonds):
                iatp = self.beads[bd.i].uname;jatp = self.beads[bd.j].uname 
                pot = 'harm';par = coeffs[i]
                bd.r = par[0]
                bd.setpar(iatp, jatp, pot, par)
                print('         ',bd.__str__())
        
        if self.angle_num > 0: 
            print('      ANGLES:')
            coeffs = cal_force_coeff(self.angles,kBT,flag='angle',label='AA')
            for i,an in enumerate(self.angles):
                iatp = self.beads[an.i].uname;jatp = self.beads[an.j].uname
                katp = self.beads[an.k].uname
                pot = 'harm';par = coeffs[i]
                an.theta = par[0]
                an.setpar(iatp, jatp, katp, pot, par)
                print('         ',an.__str__())
        
        if self.dihed_num > 0:
            print('      DIHERALS:') 
            coeffs = cal_force_coeff(self.diheds,kBT,flag='dihedral',label='AA')
            for i,dh in enumerate(self.diheds):
                iatp = self.beads[dh.i].uname;jatp = self.beads[dh.j].uname
                katp = self.beads[dh.k].uname;latp = self.beads[dh.l].uname
                pot = 'opls';par = coeffs[i][1:]
                dh.phi = coeffs[i][0]
                dh.setpar(iatp, jatp, katp, latp, pot, par)
                print('         ',dh.__str__())
    
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
        print('   Write .zmat and .ff files for %s ...' %self.mol_name)
        filename = self.AAdirectory+'./%s_CG.zmat' %self.mol_name
        f = open(filename, 'w')
        f.write('%s_CG\n'%self.mol_name)
        f.write('\n')

        bond_indices = [] # not additional bond
        for i in range(self.bead_num):
            leading_bd = self.find_leading_bond(i)
            leading_an = self.find_leading_angle(i)
            leading_dh = self.find_leading_dihed(i)
            if leading_dh:
                dh = leading_dh
                an = self.find_angle(dh.i,dh.j,dh.k)
                bd = self.find_bond(dh.i,dh.j)
                bond_indices.append(self.bonds.index(bd))
                # id name id bond id angle id dihedral
                f.write('%3d  %6s  %3d  %8.3f  %3d  % 8.3f  %d  % 8.3f\n' %(i+1,
                        self.beads[i].uname,dh.j+1,bd.r,dh.k+1,an.theta,dh.l+1,dh.phi))
            elif leading_an :
                an = leading_an
                bd = self.find_bond(an.i,an.j)
                bond_indices.append(self.bonds.index(bd))
                # id name id bond id angle
                f.write('%3d  %6s  %3d  %8.3f  %3d  % 8.3f\n' %(i+1,
                        self.beads[i].uname,an.j+1,bd.r,an.k+1,an.theta))
            elif leading_bd :
                bd = leading_bd
                bond_indices.append(self.bonds.index(bd))
                # id name id bond
                f.write('%3d  %6s  %3d  %8.3f\n' %(i+1,
                        self.beads[i].uname,bd.j+1,bd.r))
            else:
                f.write('%3d  %6s\n' %(i+1,self.beads[i].uname))
        f.write('\n')

        # add more connection info.
        if len(bond_indices) < self.bond_num:
            for i in range(self.bond_num):
                if i not in bond_indices:
                     f.write('connect %d %d\n'%(self.bonds[i].i+1,self.bonds[i].j+1)) # add connet info.
        f.write('\n')
        
        # add force field file
        f.write('%s_CG.ff\n'%self.mol_name)
        f.close()
            

        # force field file
        filename = self.AAdirectory+'./%s_CG.ff' %self.mol_name
        f = open(filename, 'w')
        f.write('# non-bond potential: lj \n')
        f.write('# bond and angle potential: k/2(x-x0)^2 \n')
        f.write('# dihedral potential: opls \n')
        f.write('\n')

        #atoms
        f.write('ATOMS\n')
        f.write('# name    name    mass     charge    lj   sigma(A)      epsilon(kJ/mol)\n')
        for bead in self.beads:
            #name name mass charge lj sigma epsilon
            f.write('%6s  %6s  %8.3f  % 8.3f   %2s   0.00   0.00\n'
                    %(bead.uname,bead.uname,bead.mass,bead.charge,'lj'))
        f.write('\n')

        #bonds
        f.write('BONDS\n')
        f.write('# name    name    harm    x0(A)   k(kJ/mol/A-2)\n')
        for bd in self.bonds:
            # name name pot x0 k
            f.write('%6s  %6s  %6s  % 8.3f   %6d\n'
                    %(self.beads[bd.i].uname,self.beads[bd.j].uname,
                    bd.pot,bd.par[0],bd.par[1])) 
        f.write('\n')

        #angles
        f.write('ANGLES\n')
        f.write('# name    name    name   harm    x0(deg)   k(kJ/mol/rad-2)\n')
        for an in self.angles:
            # name name name harm x0 k
            f.write('%6s  %6s  %6s  %6s  % 8.3f   %6d\n'
                    %(self.beads[an.i].uname,self.beads[an.j].uname,self.beads[an.k].uname,
                    an.pot,an.par[0],an.par[1]))
        f.write('\n')

        #diherals
        f.write('DIHEDRALS\n')
        f.write('# name    name    name    name   harm    k1(KJ/mol)    k2(KJ/mol)   k3(KJ/mol)   k4(KJ/mol)\n')
        for dh in self.diheds:
            # name name name name opls k1 k2 k3 k4
            f.write('%6s  %6s  %6s  %6s  %6s  % 8.3f   % 8.3f   % 8.3f   % 8.3f\n'
                    %(self.beads[dh.i].uname,self.beads[dh.j].uname,self.beads[dh.k].uname,self.beads[dh.l].uname,
                    dh.pot,dh.par[0],dh.par[1],dh.par[2],dh.par[3]))
        f.write('\n')

        f.close()

    def cal_BAD_from_CG(self,interval):
        '''calcualte bond, angle, dihedral potentials from the CG simulation'''
        if self.bond_num == 0: return
        print('   Calulcate CG bond, angle and diherdal distribution from CG simulation ...')
    
        allCOGs = self.cal_COGs(interval,label='CG')
        allBADs = self.cal_BADs(allCOGs)
        self.cal_BAD_distribution(allBADs,label='CG')

    def update_force_constant(self,kBT,frac=0.5):
        '''update force constant from the CG simulation'''
        print('   Fit bond, angle and diherdal potentials in CG simulaiton ...')
        if self.bond_num > 0:
            print('      BONDS:')
            coeffs = cal_force_coeff(self.bonds,kBT,flag='bond',label='CG')
            for i,bd in enumerate(self.bonds):
                bd.par = bd.par+frac*(bd.par-coeffs[i])
                print('         ',bd.__str__())
        
        if self.angle_num > 0: 
            print('      ANGLES:')
            coeffs = cal_force_coeff(self.angles,kBT,flag='angle',label='CG')
            for i,an in enumerate(self.angles):
                an.par = an.par+frac*(an.par-coeffs[i])
                print('         ',an.__str__())
        
        if self.dihed_num > 0:
            print('      DIHERALS:') 
            coeffs = cal_force_coeff(self.diheds,kBT,flag='dihedral',label='CG')
            for i,dh in enumerate(self.diheds):
                dh.par = dh.par+frac*(dh.par-coeffs[i,1:])
                print('         ',dh.__str__())

    def compare_BAD_AA_CG(self):
        if self.bond_num == 0: return
        print('   Compare bonds, angles and diherdals ...')
        
        if self.bond_num > 0:
            print('      BONDS:')
            compare_BAD(self.bonds,flag='bond')

        if self.angle_num > 0:
            print('      ANGLES:')
            compare_BAD(self.angles,flag='angle')

        if self.dihed_num > 0:
            print('      DIHEDRALS:')
            compare_BAD(self.diheds,flag='dihedral')