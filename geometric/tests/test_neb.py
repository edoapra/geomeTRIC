"""
A set of tests for NEB calculations
"""

import os, json, copy
from . import addons
import geometric
import tempfile
import numpy as np
from qcelemental.models import Molecule as qcmol

localizer = addons.in_folder
datad = addons.datad
exampled = addons.exampled

def test_hcn_neb_input(localizer):
    """
    Test lengths of input chains
    """
    chain_M = geometric.molecule.Molecule(os.path.join(datad, 'hcn_neb_input.xyz'))

    nimg = 7
    M1, engine = geometric.prepare.get_molecule_engine(
        input=os.path.join(datad, 'hcn_neb_input.psi4in'),
        chain_coords=os.path.join(datad, 'hcn_neb_input.xyz'),
        images=nimg,
        neb=True,
        engine='psi4'
    )

    M2, engine = geometric.prepare.get_molecule_engine(
        input=os.path.join(datad, 'hcn_neb_input.psi4in'),
        chain_coords=os.path.join(datad, 'hcn_neb_input.xyz'),
        images=50,
        neb=True,
        engine='psi4'
    )

    assert nimg == len(M1)
    assert len(M2) == len(chain_M)

@addons.using_psi4
def test_hcn_neb_optimize(localizer):
    """
    Optimize a HCN chain
    """
    M, engine = geometric.prepare.get_molecule_engine(
        input=os.path.join(datad, 'hcn_neb_input.psi4in'),
        chain_coords=os.path.join(datad, 'hcn_neb_input.xyz'),
        images=11,
        neb=True,
        engine='psi4'
    )

    params = geometric.params.NEBParams(**{'optep':True})
    chain = geometric.neb.ElasticBand(M, engine=engine, tmpdir=tempfile.mkdtemp(), params=params, plain=0)

    assert chain.coordtype == 'cart'

    final_chain, optCycle = geometric.neb.OptimizeChain(chain, engine, params)

    assert optCycle < 10
    assert final_chain.maxg < params.maxg
    assert final_chain.avgg < params.avgg

@addons.using_psi4
def test_hcn_neb_optimize_ew(localizer):
    """
    Optimize a HCN energy weighted chain.
    """
    M, engine = geometric.prepare.get_molecule_engine(
        input=os.path.join(datad, 'hcn_neb_input.psi4in'),
        chain_coords=os.path.join(datad, 'hcn_neb_input.xyz'),
        images=11,
        neb=True,
        engine='psi4'
    )

    params = geometric.params.NEBParams(**{'nebew': 10})
    chain = geometric.neb.ElasticBand(M, engine=engine, tmpdir=tempfile.mkdtemp(), params=params, plain=0)
    final_chain, optCycle = geometric.neb.OptimizeChain(chain, engine, params)

    assert optCycle < 10
    assert final_chain.maxg < params.maxg
    assert final_chain.avgg < params.avgg

@addons.using_qcelemental
def test_hcn_neb_service(localizer):
    """
    Testing QCFractal NEB service
    """
    chain_M = geometric.molecule.Molecule(os.path.join(datad, 'hcn_neb_service.xyz'))
    coords = [M.xyzs for M in chain_M]
    qcel_mols = [qcmol(symbols=chain_M[0].elem, geometry=coord, molecular_charge=0, molecular_multiplicity=1)
                      for coord in coords]

    # 1) neb.arrange()

    new_qcel_mols = geometric.neb.arrange(qcel_mols)
    count = sum([1 if not np.allclose(i.geometry, j.geometry) else 0 for i, j in zip(qcel_mols, new_qcel_mols)])
    # 5 images should change from the arrange().
    assert count == 5

    # 2) neb.prepare()
    with open(os.path.join(datad, 'prepare_json_in.json')) as prepare_in:
        in_dict = json.load(prepare_in)

    input_dict = copy.deepcopy(in_dict)
    new_coords, out_dict  = geometric.neb.prepare(input_dict)
    new_coords_ang = np.array(new_coords[0]) * geometric.nifty.bohr2ang
    old_coords_ang = out_dict['coord_ang_prev'][0]

    assert np.allclose(new_coords_ang, old_coords_ang)
    # After prepare(), there should be just 1 Ys, GWs, and GPs
    assert 1 == len(out_dict['Ys'])
    assert 1 == len(out_dict['GWs'])
    assert 1 == len(out_dict['GPs'])

    # Input gradients and previous result gradients should be identical
    input_grad = in_dict['gradients']

    for i in range(len(input_grad)):
        assert np.allclose(input_grad[i], out_dict['result_prev'][i]['gradient'])

    # 3) neb.nextchain()
    with open(os.path.join(datad, 'nextchain_json_in.json')) as prepare_in:
        in_dict = json.load(prepare_in)

    input_dict = copy.deepcopy(in_dict)
    new_coords, out_dict  = geometric.neb.nextchain(input_dict)

    new_coords_ang = np.array(new_coords[0]) * geometric.nifty.bohr2ang
    old_coords_ang = out_dict['coord_ang_prev'][0]

    assert np.allclose(new_coords_ang, old_coords_ang)
    print(in_dict['Ys'])
    print(out_dict['Ys'])

    # Output dictionary should have one more Ys, GWs, and GPs than input
    assert len(in_dict['Ys']) + 1 == len(out_dict['Ys'])
    assert len(in_dict['GWs']) + 1 == len(out_dict['GWs'])
    assert len(in_dict['GPs']) + 1 == len(out_dict['GPs'])

    # geometry needs to be emptied.
    assert len(out_dict['geometry']) == 0

    # Input gradients and previous result gradients should be identical
    input_grad = in_dict['gradients']

    for i in range(len(input_grad)):
        assert np.allclose(input_grad[i], out_dict['result_prev'][i]['gradient'])





