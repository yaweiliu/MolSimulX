# Lammps

**A Large-scale Atomic/Molecular Massively Parallel Simulator**

---

**Yawei Liu**

*2021/12/28*

- [Lammps](#lammps)
  - [how to compile your own Lammps](#how-to-compile-your-own-lammps)
  - [how to compile your own Lammps with CONP2](#how-to-compile-your-own-lammps-with-conp2)

## how to compile your own Lammps

* **Note**:you can skip installing `openmpi` and `fftw3` if you are going to use intel MKL
* install openmpi
  * in Mac `brew install openmpi`
  * in Ubuntu
    * download latest [openmpi](https://www.open-mpi.org/)
    * `tar zxvf <openmpi***.tar.gz>`
    * `cd </path/to/openmpi>`
    * `./configure --prefix=$HOME/usr/openmpi`
    * `make -j4 all; make install`
    * add openmpi to the PATH environment variable (e.g. in `.bashrc`)
      * `export PATH=$HOME/usr/openmpi/bin:$PATH`
      * `export LD_LIBRARY_PATH=$HOME/usr/openmpi/lib:$LD_LIBRARY_PATH`
* install fftw
  * in Mac `brew install fftw`
  * in Ubuntu
    * download latest [fftw](https://www.fftw.org/)
    * `tar zxvf <fftw***.tar.gz>`
    * `cd </path/to/fftw>`
    * `./configure --prefix=$HOME/usr/fftw --enable-mpi --enable-shared=yes --enable-single`
    * `make -j4 all; make install`
    * add fftw to the PATH environment variable (e.g. in `.bashrc`)
      * `export PATH=$HOME/usr/fftw/bin:$PATH`
      * `export LD_LIBRARY_PATH=$HOME/usr/fftw/lib:$LD_LIBRARY_PATH`
* install lammps
  * download latest [lammps](https://www.lammps.org/)
  * `tar zxvf <lammps***.tar.gz>`
  * `cd </path/to/lammps>`
  * `mkdir build`
  * `cd build`
  * if use fftw3: `cmake -C ../cmake/presets/most.cmake -D BUILD_SHARED_LIBS=on -D LAMMPS_EXCEPTIONS=on -D PKG_PYTHON=on -D FFT=FFTW3 -D FFT_SINGLE=no -DCMAKE_INSTALL_PREFIX=$HOME/usr/lammps ../cmake`
  * if use MKL: `cmake -C ../cmake/presets/most.cmake -D BUILD_SHARED_LIBS=on -D LAMMPS_EXCEPTIONS=on -D PKG_PYTHON=on -D FFT=MKL -D FFT_SINGLE=no -DCMAKE_INSTALL_PREFIX=$HOME/usr/lammps ../cmake`
  * `cmake --build .`
  * `cmake --install .`
  * add lammps to the PATH environment variable (e.g. in `.bashrc`)
    * `export LD_LIBRARY_PATH=$HOME/usr/lammps/lib:$LD_LIBRARY_PATH` or/and
    * `export LD_LIBRARY_PATH=$HOME/usr/lammps/lib64:$LD_LIBRARY_PATH`

## how to compile your own Lammps with [CONP2](https://github.com/srtee/lammps-USER-CONP2)

* download lammps-27May2021.tar.gz from [here](https://download.lammps.org/tars/index.html)
* `tar zxvf <lammps***.tar.gz>`
* download conp2 via ```git clone https://github.com/srtee/lammps-USER-CONP2.git```
* `cd lammps-USER-CONP2`
* `export LAMMPS_PREFIX=/path/to/lammps`
* `bash ./install_cmake.sh`
* `cd </path/to/lammps>`
* `mkdir build`
* `cd build`
  * if use fftw3: `cmake -C ../cmake/presets/most.cmake -D BUILD_SHARED_LIBS=on -D LAMMPS_EXCEPTIONS=on -D PKG_PYTHON=on -D FFT=FFTW3 -D FFT_SINGLE=no -D PKG_USER-CONP2=on -DCMAKE_INSTALL_PREFIX=$HOME/usr/lammps ../cmake`
  * if use MKL: `cmake -C ../cmake/presets/most.cmake -D BUILD_SHARED_LIBS=on -D LAMMPS_EXCEPTIONS=on -D PKG_PYTHON=on -D FFT=MKL -D FFT_SINGLE=no -D PKG_USER-CONP2=on -DCMAKE_INSTALL_PREFIX=$HOME/usr/lammps ../cmake`
* `cmake --build .`
* `cmake --install .`
* add lammps to the PATH environment variable (e.g. in `.bashrc`)
  * `export PATH=$HOME/usr/lammps/bin:$PATH`
  * `export LD_LIBRARY_PATH=$HOME/usr/lammps/lib:$LD_LIBRARY_PATH` or/and
  * `export LD_LIBRARY_PATH=$HOME/usr/lammps/lib64:$LD_LIBRARY_PATH`