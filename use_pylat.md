# PyLAT

**A python tool (based Python 2) to analyze the trajectories generated by LAMMPS**

---

**Shuting Xu**

*2022/8/19*

- [PyLAT](https://github.com/MaginnGroup/PyLAT)
  - [install](#install)
  - [scripts file](#scripts-file)
  - [topology file](#topology-file)
  - [trajectory file](#trajectory-file)
  - [log file](#log-file)

## install

* download the complete folder；
* complie : `sh compile.sh`

## scripts file

* python  \
`/home/stxu/PyLAT-master/PyLAT.py \`&emsp; #PyLAT Path          
`-T 300 \`&emsp; #Temperature   
`--nummol 420 --nummol 430 --nummol 105 \`&emsp; #the number of molecules / ions  
`--mol Bmim --mol Br --mol H2O \`&emsp;#the name of molecules / ions  
`--IPL \`&emsp;#calculated properties    
`-v 2 \`&emsp;#default   
`-p /lustre/stxu/under/2-UA-run/0.2/420 \`&emsp; #output path   
`log.eq1 \`&emsp; #log file name   
`data.lammps \`&emsp; #topo file name   
`dump.011 \`&emsp; #trajectory file name  
`-f ipl.json`&emsp; #output file name

* The order of numbers and the names must correspond.
* The parameters of calculated properties can be obatained in [PyLAT.py](https://gitee.com/yliu3803/MolSimulX/tree/master/postprocess/PyLAT/PyLAT.py).

## topology file

* The formats accepted by PyLAT are data file ouput by lammps.*(such as data.lammps,data,lmp)*
* Each file contains the force field information.
* See an [example](https://gitee.com/yliu3803/MolSimulX/blob/master/example_water_between_two_walls/data.lmp)

## trajectory file

* **Output format**\
 `dump mytrajectory fluid custom 2000 dump.011 id mol type x y z ix iy iz`
* PyLAT could analyze several trajectories at the same time.   
`dump.011 dump.012 dump.013 \`


## log file

* The log file must include all the calculated trajectory.
* The log file must have `timestep n` in it.