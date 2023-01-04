# fftool

**A python tool to create initial files for molecular dynamics simulatons**

---

**Yawei Liu**

*2021/11/30*

- [fftool](#fftool)
  - [before use](#before-use)
  - [topology file](#topology-file)
  - [force field file (.ff file)](#force-field-file-ff-file)
  - [use fftool](#use-fftool)

## before use

* [python](https://www.python.org/) and [packmol](http://leandro.iqm.unicamp.br/m3g/packmol/home.shtml) are required.
* [pypy](https://www.pypy.org/) is recommened for large systems.

* fftool needs two types of files for each species (molecules, ions and other materials) in MD simulations
  *  a topology file with atomic coordinates and eventually connectivity (covalent bonds)
  *  a force field file with parameters for the masses, the atomic charges, non-bond interactions and bond (including bond, angle, diheral and improper) interactions.
  *  you can find some examples in [example](./preprocess/fftool/examples)

* **alway test your files with a minimal system**

* More detailed information can be found [here](./preprocess/fftool).

## topology file

* The formats accepted by fftool are `.zmat`, `.xyz`, `.pdb` or `.mol`.
* Each file contains the filename for the force field.
* fftool can deduce the connectivity between atoms based on the bond length in the force field file.
    * reconnect is always performed for `.xyz` and `.pbd` files.
    * reconnect is performed for `.zmat` and `.mol` files if a `reconnect` keyword is given.


* `.zmat` file is always recommend, especially for building an own custom molecule.
  * this is an example for benzene
  ```
  benzene

  CA
  CA  1  rCC
  CA  2  rCC  1  120.00
  CA  3  rCC  2  120.00  1   0
  CA  4  rCC  3  120.00  2   0
  CA  5  rCC  4  120.00  3   0
  HA  1  rCH  2  120.00  3 180
  HA  2  rCH  3  120.00  4 180
  HA  3  rCH  4  120.00  5 180
  HA  4  rCH  5  120.00  6 180
  HA  5  rCH  6  120.00  1 180
  HA  6  rCH  1  120.00  2 180

  rCC = 1.400
  rCH = 1.080

  connect 1 6

  oplsaa.ff
  ```
  * the first atom `CA` is at the center
  * the second atom `CA` is connected to the first one by a bond with length of `rCC`
  * the third atom `CA` is connected to the second one by a bond with length of `rCC`, forming an angle of 120$^\circ$ between 3-2-1 atoms.
  * the fourth atom `CA` is connected to the third one by a bound with length of `rCC`, forming an angle of 120$^\circ$ between 4-3-2 atoms and an diherial of 0$^\circ$.
  * etc.
  * in this case cyclic molecules require additional connect records to close rings: `connect 1 6`.
  * improper dihedrals can be indicated by improper records (note that fftool assumes the central atom of the improper dihedral to be the third in the list).
  * the filename of the force field file (`oplsaa.ff`) is given at last.

## force field file (.ff file)

* see an example for .ff file in [example](./preprocess/fftool/examples).
* Be careful of the units in .ff file:
    * the distance unit is `A`.
    * the angle unit is `deg`.
    * the energy unit is `KJ/mol` (**different from `Kcal/mol` for LAMMPS real units**, $1\text{Kcal}\approx4.184\text{KJ}$)
    * the unit of spring constant for harmonic bonds is `kJmol-1A-2`
    * the unit of spring constant for harmonic angles is `kJmol-1rad-2`
* Be careful of the formula of harmonic potential in .ff file:
  * bond and angle force constants are in the form $k/2 (x - x_0)^2$ (**different from that of LAMMPS in which it is $k (x - x_0)^2$**).
* manual editing of the files is usually necessary in order to match the atom names with those of the force field.

## use fftool

* `fftool -h` gives all help information.
* An example to build a simulation box with 40 ethanol and 300 water molecules and a density of 38.0 mol/L:
  * `fftool 40 ethanol.zmat 300 spce.zmat -r 38.0 -c` # -c put the center of box in the origin
  * `packmol < pack.inp` 
  * `fftool 40 ethanol.zmat 300 spce.zmat -r 38.0 -c -l` # -l for creating inital files for LAMMPS