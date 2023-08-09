#!/bin/bash
#export ASE_NWCHEM_COMMAND="mpirun -np 3 /data/edo/nwchem/nwchemgit/bin/LINUX64/nwchem PREFIX.nwi > PREFIX.nwo"
geometric-optimize --ase-class=ase.calculators.nwchem.NWChem \
--ase-kwargs='{"memory":"total 1024 mb noverify",
	       "center":"True",
	       "autosym":"True",
 	       "geompar":" store_symrot",
	       "dft":"; xc xpbe96 cpbe96; disp vdw 4; mult 1; noio ; convergence fast; vectors input nwchem.movecs; end" ,
	       "basis \"cd basis\"  spherical":"; * library weigend_coulomb_fitting;  end",
 	       "basis":"def2-svpd", 
	       "basispar":"spherical"}' \
		   --engine ase  water6.xyz \
		   --qdata YES
