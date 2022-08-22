# Lammps

**A Large-scale Atomic/Molecular Massively Parallel Simulator**

---

**Yawei Liu**

*2021/12/28*

- [Lammps](#lammps)
  - [how to compile your own Lammps](#how-to-compile-your-own-lammps)

## how to compile your own Lammps

* install openmpi
  * in Mac ```brew install openmpi```
  * in Ubuntu
    * download latest [openmpi](https://www.open-mpi.org/)
    * ```tar zxvf openmpi***.tar.gz```
    * ```cd openmpi```
    * ```./configure --prefix=$HOME/usr/openmpi```
    * ```make -j4 all; make install```
    * add openmpi to the PATH environment variable (e.g. in ```.bashrc```)
      * ```export PATH=$HOME/usr/openmpi/bin:$PATH```
      * ```export LD_LIBRARY_PATH=$HOME/usr/openmpi/lib:$LD_LIBRARY_PATH```
* install fftw
  * in Mac ```brew install fftw```
  * in Ubuntu
    * download latest [fftw](https://www.fftw.org/)
    * ```tar zxvf fftw***.tar.gz```
    * ```cd fftw```
    * ```./configure --prefix=$HOME/usr/fftw --enable-mpi --enable-shared=yes --enable-single```
    * ```make -j4 all; make install```
    * add fftw to the PATH environment variable (e.g. in ```.bashrc```)
      * ```export PATH=$HOME/usr/fftw/bin:$PATH```
      * ```export LD_LIBRARY_PATH=$HOME/usr/fftw/lib:$LD_LIBRARY_PATH```
* install lammps
  * download latest [lammps](https://www.lammps.org/)
  * ```tar zxvf lammps***.tar.gz```
  * ```cd lammps```
  * ```mkdir build```
  * ```cd build```
  * ```cmake -C ../cmake/presets/most.cmake -D BUILD_SHARED_LIBS=on -D LAMMPS_EXCEPTIONS=on -D FFT=FFTW3 -D FFT_SINGLE=yes -DCMAKE_INSTALL_PREFIX=$HOME/usr/lammps ../cmake```
  * ```cmake --build .```
  * ```cmake --install .```
  * add lammps to the PATH environment variable (e.g. in ```.bashrc```)
    * ```export PATH=$HOME/usr/lammps/bin:$PATH```
    * ```export LD_LIBRARY_PATH=$HOME/usr/lammps/lib:$LD_LIBRARY_PATH```