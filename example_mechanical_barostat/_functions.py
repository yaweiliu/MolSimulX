import MDAnalysis as mda

atomic_wt = {'H': 1.008, 'Li': 6.941, 'B': 10.811, 'C': 12.011,
             'N': 14.006, 'O': 15.999, 'F': 18.998, 'Ne': 20.180,
             'Na': 22.990, 'Mg': 24.305, 'Al': 26.982, 'Si':  28.086,
             'P': 30.974, 'S': 32.065, 'Cl': 35.453, 'Ar': 39.948,
             'K': 39.098, 'Ca': 40.078, 'Ti': 47.867, 'Fe': 55.845,
             'Zn': 65.38, 'Se': 78.971, 'Br': 79.904, 'Kr': 83.798,
             'Mo': 95.96, 'Ru': 101.07, 'Sn': 118.710, 'Te': 127.60,
             'I': 126.904, 'Xe': 131.293}

# Takes in a file path to open, what string you start splitting at, and the indexing for each line
def fetchList(filePath, splitString, indexingStart, indexingEnd='None', skipBlankSplit=False, *args):
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
                    if is_number(ar):
                        importantLine += [(currentLine.split())[ar]]
                listArray.append(importantLine)  # Append the important line to the list array
        if splitString in currentLine:  # Check at the end because we only want to start splitting after the string; if found, it'll split all further lines till it gets to white space
            readMode = True
    openedFile.close()
    return listArray  # Return the array containing all associations



def read_traj(topo,traj,ilnum,waternum):
    u = mda.Universe(topo, atom_style='id resid type charge x y z')
    # add elements
    elements = []
    for i in range(len(u.atoms)):
        elements.append(chemical_symbols[np.where(types==int(u.atoms[i].type))[0][0]])
    u.add_TopologyAttr('element',values=elements)

    # add mol. name
    if waternum == 0:
        resnames = ['cation']*ilnum+['anion']*ilnum
    else:
        resnames = ['cation']*ilnum+['anion']*ilnum +['water']*waternum
    u.add_TopologyAttr('resnames',values=resnames)
    
    u.load_new(traj,format="LAMMPSDUMP",timeunit="fs",dt=10000)
    workflow = [transformations.unwrap(u.atoms)]
    u.trajectory.add_transformations(*workflow)
    return u

def atomic_symbol(name):
    if name[:2] in atomic_wt:
        return name[:2]
    elif name[0] in atomic_wt:
        return name[0]
    else:
        print('warning: unknown symbol for atom ' + name)
        return name