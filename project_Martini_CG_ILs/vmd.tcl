### set color
color change rgb  0 0.122 0.467 0.706 ;# blue
color change rgb  1 0.7 0.2 0.1 ;# red
color change rgb  2 0.4 0.4 0.4 ;# grey
color change rgb  3 0.7 0.4 0.0 ;# orange
color change rgb  4 0.74 0.74 0.13 ;# yellow
color change rgb  7 0.17 0.63 0.17 ;# green
color change rgb 9 0.89 0.47 0.76 ;# pink
color change rgb 10 0.09 0.75 0.81 ;# cyan
color change rgb 11 0.58 0.40 0.74 ;# purple

### set element color
color Element C 2
color Element B 1
color Element F 20

### change material 'Diffuse'
material change ambient Diffuse 0.00
material change specular Diffuse 0.0
material change diffuse Diffuse 0.9
material change shininess Diffuse 0.7
material change opacity Diffuse 1.0
material change outline Diffuse 4.
material change outlinewidth Diffuse 1.


### make sure, that the main menu is active
menu main on
### modify display settings
display projection orthographic
### orthographic
axes location off
color Display Background white
### view
#rotate x by -90
scale by 2


### delete current molecules & load new molecules
if {[molinfo num] > 0} { 
  mol delete all
}

### loal molecules
set fname "result_atoms.xyz"
mol new $fname waitfor all
#topo readvarxyz result_atoms.xyz

### delete all rep
set numrep [molinfo top get numreps]
for {set i 0} {$i < $numrep} {incr i} {mol delrep $i top}

set numatom [molinfo top get numatoms]
set numframe [molinfo top get numframes]

### defualt 
mol selection all
mol representation VDW 1.0 30.0
mol material Diffuse
mol color colorID 0

### connections
set fname "result_connect.dat"
set nskipline 0
#itype=0 means reset connectivity by user-defined list, 
#     =1 means add self-defined connectivity list to the original one
set itype 0
set rdpdbcon [open $fname r]

#Skip other lines
for {set i 1} {$i<=$nskipline} {incr i} {
gets $rdpdbcon line
}

#Cycle each atom
set ird 1
for {set iatm 1} {$iatm<=$numatom} {incr iatm} {

if {$ird==1} {
 for {set i 1} {$i<=12} {incr i} {set cn($i) 0}
 gets $rdpdbcon line
 scan [string range $line 6 200] "%d %d %d %d %d %d %d %d %d %d %d %d %d" self cn(1) cn(2) cn(3) cn(4) cn(5) cn(6) cn(7) cn(8) cn(9) cn(10) cn(11) cn(12)

 set tmplist {}
 #Formation of connectivity list
 for {set i 1} {$i<=12} {incr i} {
  if {$cn($i)==0} {break}
  lappend tmplist [expr $cn($i)-1]
 }
}

if {$self==$iatm} {
 #puts Atom\ serial:\ $iatm\ \ User-connectivity:\ $tmplist
 set sel [atomselect top "serial $iatm"]
 if {$itype==0} {
  $sel setbonds "{$tmplist}"
 } else {
  set orglist [$sel getbonds]
  $sel setbonds "{[concat [lindex $orglist 0] $tmplist]}"
 }
 $sel delete
 set ird 1
} else {
 set ird 0
}
}
close $rdpdbcon

### size
set all [atomselect top "all"]
$all set radius 1

### reps
mol selection "element C or element N"
mol addrep top
mol modstyle 0 top Licorice 0.7 60 60
mol modcolor 0 top Element
mol selupdate 0 top on

mol selection "element B or element F"
mol addrep top 
mol modstyle 1 top Licorice 0.7 60 60
mol modcolor 1 top Element
mol selupdate 1 top on

### set box boundary
set fname "result_box.dat"
set in [open $fname r]
set cell {}
while { [gets $in line] != -1 } { lappend cell $line}
pbc set $cell -all
#pbc wrap -center unitcell -compound res
pbc box -center unitcell -color orange -width 5