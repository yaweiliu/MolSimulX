import numpy as np
import re
import MDAnalysis as mda
from MDAnalysis import transformations
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt

from _external_constants import *

#---------------------------------------------------------------------------------------------
def read_traj(topo,traj,num,atom_types,chemical_symbols):
    '''read LAMMPS trajectory by mdanalysis'''
    u = mda.Universe(topo, atom_style='id resid type charge x y z')
    # add elements
    elements = []
    for i in range(len(u.atoms)):
        elements.append(chemical_symbols[np.where(atom_types==int(u.atoms[i].type))[0][0]])
    u.add_TopologyAttr('element',values=elements)
    u.add_TopologyAttr('element',values=elements)

    # add mol. name
    resnames = ['cation']*num+['anion']*num
    u.add_TopologyAttr('resnames',values=resnames)
    
    u.load_new(traj,format="LAMMPSDUMP",timeunit="fs",dt=10000)
    workflow = [transformations.unwrap(u.atoms)]
    u.trajectory.add_transformations(*workflow)

    print('There are %d frames in %s and %s' %(u.trajectory.n_frames,topo,traj))
    return u  

def write_pdb(u,bonds=None,interval=1):
    '''write mdanalysis universe into a pdb file, with the real-time box size'''
    f = open("result_box.dat",'w')
    with mda.Writer("result_atoms.pdb", multiframe=True, bonds=bonds, n_atoms=u.atoms.n_atoms) as PDB:
        u.trajectory[0]
        for ts in u.trajectory[::interval]:
            PDB.write(u.atoms)
            f.write('%.6f %.6f %.6f\n' %(ts.dimensions[0],ts.dimensions[1],ts.dimensions[2]))
    f.close()
    return

def write_xyz(u,connect=False,interval=1):
    '''write mdanalysis universe into xyz file, box size into file, and/or connect information '''
    f = open("result_box.dat",'w')
    with mda.Writer("result_atoms.xyz", u.atoms.n_atoms) as XYZ:
        u.trajectory[0]
        for ts in u.trajectory[::interval]:
            XYZ.write(u.atoms)
            f.write('%.6f %.6f %.6f\n' %(ts.dimensions[0],ts.dimensions[1],ts.dimensions[2]))
    f.close()
    if connect:
        f = open("result_connect.dat",'w')
        for i in range(u.atoms.n_atoms):
            sel = u.select_atoms('index %d' %i)
            connect = ['%s' %sel.atoms[0].id]
            for bd in sel.bonds:
                if bd.atoms[0].id == sel.atoms[0].id: connect.append('%s' %bd.atoms[1].id)
                else: connect.append('%s' %bd.atoms[0].id)
            f.write('CONECT '+' '.join(connect)+'\n')
    return


def type_element(filename):
    '''return elements for types in LAMMPS based on data.lmp generated by fftool'''
    elements = fetchList(filename, 'Masses', 0,4, skipBlankSplit=True)
    digitspattern = r'#'
    atom_types = []
    chemical_symbols = []
    for element in elements:
        atom_types.append(int(element[0]))
        txt = re.sub(digitspattern, '', element[-1])
        chemical_symbols.append(atomic_symbol(txt))
    atom_types = np.array(atom_types)

    print('atom types:       ',atom_types)
    print('chemical symbols: ',chemical_symbols)
    return atom_types,chemical_symbols 

def atomic_symbol(name):
    '''return atom name in periodic table'''
    if name[:2] in atomic_wt:
        return name[:2]
    elif name[0] in atomic_wt:
        return name[0]
    else:
        #print('warning: unknown symbol for atom ' + name)
        return name

def fetchList(filePath, splitString, indexingStart, indexingEnd='None', skipBlankSplit=False, *args):
    '''Takes in a file path to open, what string you start splitting at, and the indexing for each line'''
    readMode = False
    openedFile = open(filePath, 'r')
    listArray = []
    currentLine = ''
    for line in openedFile:
        previousLine = currentLine
        currentLine = str(line)
        if currentLine.isspace() and readMode is True:  # In each line, check if it's purely white space
            # If the previous line doesn't countain the spliting string (i.e. this isn't the line directly after the split), stop reading; only occurs if the skipBlankSplit option is set to True
            if splitString not in previousLine or skipBlankSplit is False:
                readMode = False
        if currentLine[0] == '[':  # The same is true if it's the start of a new section, signalled by '['
            readMode = False
        if readMode is True:
            if line[0] != ';' and currentLine.isspace() is False:  # If the line isn't a comment
                if indexingEnd == 'None':
                    # Just split with a start point, and take the rest
                    importantLine = (currentLine.split())[indexingStart:]
                else:
                    # Define the bigt we care about as the area between index start and end
                    importantLine = (currentLine.split())[indexingStart:indexingEnd]
                # If any additional arguments were given (and they're numbers), also add this specific index in
                for ar in args:
                    if ar.isnumeric():
                        importantLine += [(currentLine.split())[ar]]
                listArray.append(importantLine)  # Append the important line to the list array
        if splitString in currentLine:  # Check at the end because we only want to start splitting after the string; if found, it'll split all further lines till it gets to white space
            readMode = True
    openedFile.close()
    return listArray  # Return the array containing all associations
#---------------------------------------------------------------------------------------------

#---------------------------------------------------------------------------------------------
def bead_symbol(uname):
    '''return name of bead in Martini3'''
    flag = True
    for i,str in enumerate(list(uname)):
        if str not in bead_letters: 
            flag = False
            break
    if flag: return uname[:i+1]
    else: return uname[:i]
#---------------------------------------------------------------------------------------------

#---------------------------------------------------------------------------------------------
def histograms(data):
    '''return histrogram of a 1D data array'''
    valmin = np.min(data)
    valmax = np.max(data)
    binN = 100
    count,edges = np.histogram(data,bins = np.linspace(np.min(data),np.max(data),binN),density=True)
    centers = .5 * (edges[:-1] + edges[1:])
    return centers,count

def cal_bond(p0,p1):
    return np.linalg.norm(p1-p0)
    
def cal_angle(p0,p1,p2):
    #p1 is the central point
    b0 = p0-p1; b0 /= np.linalg.norm(b0)
    b1 = p2-p1; b1 /= np.linalg.norm(b1)
    return np.arccos(np.dot(b0,b1))

def cal_dihedral(p0,p1,p2,p3):
    #p0,p1,p2,p3 in linear order
    b0 = -1.0*(p1 - p0)
    b1 = p2 - p1
    b2 = p3 - p2
    b1 /= np.linalg.norm(b1)
    v = b0 - np.dot(b0, b1)*b1
    w = b2 - np.dot(b2, b1)*b1
    x = np.dot(v, w)
    y = np.dot(np.cross(v, b1), w)
    return np.arctan2(y, x)

def gaussian(x,A,omega_inv,x0):
    '''gaussian for bond and angle'''
    return 0.7978845608028654*A*omega_inv*np.exp(-2*((x-x0)*omega_inv)**2)

def opls(x,k1,k2,k3,k4):
    '''opls for dihedral'''
    cosphi = np.cos(x)
    cos2phi = np.cos(2*x)
    cos3phi = np.cos(3*x)
    cos4phi = np.cos(4*x)
    return 0.5*k1*(1+cosphi)+0.5*k2*(1-cos2phi)+0.5*k3*(1+cos3phi)+0.5*k4*(1-cos4phi)
#---------------------------------------------------------------------------------------------


#---------------------------------------------------------------------------------------------
def anglesdiheds(bonds,natom):
    '''identify angles and dihedrals based on bond connectivity'''
    nbond = len(bonds)
    angles = []
    diheds = []

    # identify valence angles
    for i in range(natom):  # find neighbour atoms to each atom i
        nb = 0
        neib = []
        for bd in bonds:          
            if i == bd.i:
                neib.append(bd.j)
                nb += 1
            elif i == bd.j:
                neib.append(bd.i)
                nb += 1
        for k in range(nb - 1):
            for l in range(k + 1, nb):
                if neib[k]>neib[l]: angles.append([neib[k], i, neib[l]])
                else: angles.append([neib[l], i, neib[k]])
    angles.sort(reverse = True)
        
    # identify dihedral angles
    for k in range(nbond): # find bonds around non-terminal bonds
        for l in range(nbond):
            if l == k: continue
            if bonds[l].i == bonds[k].i:
                for j in range(nbond):
                    if j == k or j == l: continue
                    if bonds[j].i == bonds[k].j:
                        line = [bonds[l].j,bonds[k].i,bonds[k].j,bonds[j].j]
                        if len(set(line)) < len(line): continue
                        if line[0]<line[-1]: line.reverse()
                        diheds.append(line)
                    elif bonds[j].j == bonds[k].j:
                        line = [bonds[l].j,bonds[k].i,bonds[k].j,bonds[j].i]
                        if len(set(line)) < len(line): continue
                        if line[0]<line[-1]: line.reverse()
                        diheds.append(line)
            elif bonds[l].j == bonds[k].i:
                for j in range(nbond):
                    if j == k or j == l: continue
                    if bonds[j].i == bonds[k].j:
                        line = [bonds[l].i,bonds[k].i,bonds[k].j,bonds[j].j]   
                        if len(set(line)) < len(line): continue
                        if line[0]<line[-1]: line.reverse()
                        diheds.append(line)
                    elif bonds[j].j == bonds[k].j:
                        line = [bonds[l].i,bonds[k].i,bonds[k].j,bonds[j].i]
                        if len(set(line)) < len(line): continue
                        if line[0]<line[-1]: line.reverse()
                        diheds.append(line)

    # sort dihedrals
    diheds.sort(reverse = True)

    return angles,diheds


#---------------------------------------------------------------------------------------------
def cal_BAD_from_COGs(mol,COGs):
    '''compuate bond, angle, dihedral from COGs of bead'''
    #bonds
    bonds = []
    for bd in mol.bonds:
        x = cal_bond(COGs[bd.i],COGs[bd.j])
        bonds.append(x)
    
    #angles
    angles = []
    for an in mol.angles:
        x = cal_angle(COGs[an.i],COGs[an.j],COGs[an.k])
        angles.append(x)

    #dihedrals
    diheds = []
    for dh in mol.diheds:
        x = cal_dihedral(COGs[dh.i],COGs[dh.j],COGs[dh.k],COGs[dh.l])
        diheds.append(x)
    
    return bonds,angles,diheds

def cal_BAD_distributions(mol,u,interval,label='AA'):
    '''compute COGs for each bead from AA/CG simulaiton'''
    print('calulcate bond, angle and diherdal distribution from %s simulation ...' %label)
    mols = u.select_atoms('resname %s'%mol.resname)
    resids = np.unique(mols.atoms.resids)
    allBonds = []
    allAngles = []
    allDiheds = []
    if label == 'AA': 
        for ts in u.trajectory[::interval]:   
            for i in resids:
                sel = mols.select_atoms('resid %d'%i)
                COGs = []
                for bd in mol.beads: COGs.append(np.mean(sel.atoms.positions[bd.atom_indices],axis=0))
                bonds,angles,diheds = cal_BAD_from_COGs(mol,COGs)
                allBonds.append(bonds)
                allAngles.append(angles)
                allDiheds.append(diheds)
    else:
        for ts in u.trajectory[::interval]:   
            for i in resids:
                sel = mols.select_atoms('resid %d'%i)
                bonds,angles,diheds = cal_BAD_from_COGs(mol,sel.atoms.positions)
                allBonds.append(bonds)
                allAngles.append(angles)
                allDiheds.append(diheds)
    
    # bond distribution
    if mol.nbond == 0: return
    data = np.array(allBonds)
    for i in range(mol.nbond):
        centers,count = histograms(data[:,i])
        x0 = np.mean(data[:,i])
        if label == 'AA': mol.bonds[i].distribution_AA = [centers,count,x0]
        else: mol.bonds[i].distribution_CG = [centers,count,x0]

    # angle distribution
    if mol.nangle == 0: return
    data = np.array(allAngles)
    for i in range(mol.nangle):
        centers,count = histograms(data[:,i])
        x0 = np.mean(data[:,i])
        if label == 'AA': mol.angles[i].distribution_AA = [centers,count,x0]
        else: mol.angles[i].distribution_CG = [centers,count,x0]

    # dihedral distribution
    if mol.ndihed == 0: return
    data = np.array(allDiheds)
    for i in range(mol.ndihed):
        centers,count = histograms(data[:,i])
        x0 = np.mean(np.abs(data[:,i])) # abs value
        if label == 'AA': mol.diheds[i].distribution_AA = [centers,count,x0]
        else: mol.diheds[i].distribution_CG = [centers,count,x0]

    return

def cal_BAD_potentials(mol,kBT):
    '''calcualte bond, angle, dihedral potentials from the AA simulation'''
    if mol.nbond == 0: return
    print('calulcate bond, angle and diherdal potentials from AA simulation ...')

    if mol.nbond > 0:
        print('BONDS:')
        coeffs = cal_force_coeffs(mol.bonds,kBT,flag='bond',label='AA')
        for i,bd in enumerate(mol.bonds):
            iatp = mol.beads[bd.i].uname;jatp = mol.beads[bd.j].uname 
            pot = 'harm';par = coeffs[i]
            bd.r = par[0]
            bd.setpar(iatp, jatp, pot, par)
            print('     ',bd.__str__())
        
    if mol.nangle > 0: 
        print('ANGLES:')
        coeffs = cal_force_coeffs(mol.angles,kBT,flag='angle',label='AA')
        for i,an in enumerate(mol.angles):
            iatp = mol.beads[an.i].uname;jatp = mol.beads[an.j].uname;katp = mol.beads[an.k].uname
            pot = 'harm';par = coeffs[i]
            an.theta = par[0]
            an.setpar(iatp, jatp, katp, pot, par)
            print('     ',an.__str__())
        
    if mol.ndihed > 0:
        print('DIHERALS:') 
        coeffs = cal_force_coeffs(mol.diheds,kBT,flag='dihedral',label='AA')
        for i,dh in enumerate(mol.diheds):
            iatp = mol.beads[dh.i].uname;jatp = mol.beads[dh.j].uname
            katp = mol.beads[dh.k].uname;latp = mol.beads[dh.l].uname
            pot = 'opls';par = coeffs[i][1:]
            dh.phi = coeffs[i][0]
            dh.setpar(iatp, jatp, katp, latp, pot, par)
            print('     ',dh.__str__())
    return

def update_BAD_potentials(mol,kBT,frac=0.5):
    '''update bond, angle, dihedral potentials from the CG simulation'''
    if mol.nbond == 0: return
    print('update bond, angle and diherdal potentials from AA simulation ...')

    if mol.nbond > 0:
        print('BONDS:')
        coeffs = cal_force_coeffs(mol.bonds,kBT,flag='bond',label='CG')
        for i,bd in enumerate(mol.bonds):
            bd.par = bd.par+frac*(bd.par-coeffs[i])
            print('         ',bd.__str__())
        
    if mol.nangle > 0: 
        print('ANGLES:')
        coeffs = cal_force_coeffs(mol.angles,kBT,flag='angle',label='CG')
        for i,an in enumerate(mol.angles):
            an.par = an.par+frac*(an.par-coeffs[i])
            print('         ',an.__str__())
        
    if mol.ndihed > 0:
        print('DIHERALS:') 
        coeffs = cal_force_coeffs(mol.diheds,kBT,flag='dihedral',label='CG')
        for i,dh in enumerate(mol.diheds):
            dh.par = dh.par+frac*(dh.par-coeffs[i,1:])
            print('         ',dh.__str__())
    return

def cal_force_coeffs(data,kBT,flag,label='AA'):
    '''calcuate potential coefficients from distribution, and plot'''
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

        #for angle/dihedral, plot in degrees;
        #for dihedral, using opls
        if flag == 'bond': 
            centers_plot = centers
        elif flag == 'angle': 
            centers_plot = np.degrees(centers)
        elif flag == 'dihedral':
            args = np.where(count==0.)
            mask = np.ones(len(count), dtype=bool)
            mask[args] = False
            centers = centers[mask];count = count[mask]
            centers_plot = np.degrees(centers)
            count = -kBT*np.log(count)
            count -= count[0]
        
        ax.plot(centers_plot,count,'.',alpha=0.5)

        try:
            if flag == 'bond' or flag == 'angle':
                func = lambda x, A, omega_inv: gaussian(x, A, omega_inv, x0)
                popt,_ = curve_fit(func, centers, count)
                coeffs.append([x0,4*kBT*popt[-1]**2]) #we take k/2(x-x0)^2
            else:
                func = opls
                popt,_ = curve_fit(func, centers, count)
                coeffs.append([x0,popt[0],popt[1],popt[2],popt[3]])
            ax.plot(centers_plot,func(centers,*popt),'k--',lw=1,zorder=10)
        except RuntimeError:
            ax.plot((x0,x0),(np.min(count),np.max(count)),'k--',lw=1,zorder=10)
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

def plot_BAD_distributions(data,kBT,flag):
    '''plot distributions of AA, CG and fitting for AA'''
    N = max(4,int(np.sqrt(len(data))))
    M = int(len(data)/N)
    if M*N<len(data): M += 1
    
    fig = plt.figure(figsize=(3*N,1.5*M), dpi=140);
    ncount = 0
    coeffs = []
    for i in range(len(data)):
        ncount += 1
        ax = fig.add_subplot(int('%d%d%d'%(M,N,ncount)));
        
        # AA data
        centers,count,x0 = data[i].distribution_AA
        
        #for angle/dihedral, plot in degrees;
        #for dihedral, using opls
        if flag == 'bond': 
            centers_plot = centers
        elif flag == 'angle': 
            centers_plot = np.degrees(centers)
        elif flag == 'dihedral':
            args = np.where(count==0.)
            mask = np.ones(len(count), dtype=bool)
            mask[args] = False
            centers = centers[mask];count = count[mask]
            centers_plot = np.degrees(centers)
            count = -kBT*np.log(count)
            count -= count[0]
        
        ax.plot(centers_plot,count,'.',alpha=0.5)

        try:
            if flag == 'bond' or flag == 'angle':
                func = lambda x, A, omega_inv: gaussian(x, A, omega_inv, x0)
                popt,_ = curve_fit(func, centers, count)
            else:
                func = opls
                popt,_ = curve_fit(func, centers, count)
            ax.plot(centers_plot,func(centers,*popt),'k--',lw=1,zorder=10)
        except RuntimeError:
            ax.plot((x0,x0),(np.min(count),np.max(count)),'k--',lw=1,zorder=10)
            print("Bad fitting! Skip!")

        # CG data
        centers,count,x0 = data[i].distribution_CG
        
        #for angle/dihedral, plot in degrees;
        #for dihedral, using opls
        if flag == 'bond': 
            centers_plot = centers
        elif flag == 'angle': 
            centers_plot = np.degrees(centers)
        elif flag == 'dihedral':
            args = np.where(count==0.)
            mask = np.ones(len(count), dtype=bool)
            mask[args] = False
            centers = centers[mask];count = count[mask]
            centers_plot = np.degrees(centers)
            count = -kBT*np.log(count)
            count -= count[0]
        
        ax.plot(centers_plot,count,'.',alpha=0.5)

        if flag == 'bond': ax.set_xlabel(r'$x$ [$\AA$]');
        else: ax.set_xlabel(r'$x$ [$^\circ$]');
        ax.set_ylabel(r'$p(x)$');
        if flag == 'dihedral': ax.set_ylabel(r'$U(x)$');
        ax.tick_params(direction='in')
    
    plt.tight_layout()
    plt.show()

    return

def compare_BAD_distributions(mol,kBT):
    if mol.nbond == 0: return
    print('compare bond, angle and diherdal from AA and CG simulations ...')
    if mol.nbond > 0:
        print('BONDS:')
        plot_BAD_distributions(mol.bonds,kBT,flag='bond')
    
    if mol.nangle > 0:
        print('      ANGLES:')
        plot_BAD_distributions(mol.angles,kBT,flag='angle')

    if mol.ndihed > 0:
        print('      DIHEDRALS:')
        plot_BAD_distributions(mol.diheds,kBT,flag='dihedral')
#---------------------------------------------------------------------------------------------


#---------------------------------------------------------------------------------------------
def cal_lj_potential(bead_names,ffile='./martini_v3.0.0.itp'):
    '''search lj potentials between martini3 beads'''
    ffs = fetchList(ffile, 'nonbond_params', 0,5, skipBlankSplit=True)
    ff_names = [ff[0:2] for ff in ffs]
    ff_coeffs = np.array([list(map(float,ff[3:5])) for ff in ffs]) #simga [nm] epsilon [KJ/mol]
    
    lmp_types = np.arange(len(bead_names))+1
    filename = './pair_CG.lmp'
    print('lj parameters in %s' %filename)

    f =  open(filename,'w')
    for i in range(len(bead_names)):
        for j in range(i,len(bead_names)):
            try:
                index = ff_names.index([bead_names[i],bead_names[j]])
            except ValueError:
                index = ff_names.index([bead_names[j],bead_names[i]])
            except:   print('pair not found!')
            sigma,epsilon = ff_coeffs[index,:]
            print('pair_coeff %3d %3d %8.4f %8.4f #%6s %6s'
                  %(lmp_types[i],lmp_types[j],epsilon/4.184,sigma*10,bead_names[i],bead_names[j]))
            f.write('pair_coeff %3d %3d %8.4f %8.4f #%6s %6s\n'
                  %(lmp_types[i],lmp_types[j],epsilon/4.184,sigma*10,bead_names[i],bead_names[j]))
    f.close()
    return 
#---------------------------------------------------------------------------------------------