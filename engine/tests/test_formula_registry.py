import pytest
from research_engine.formula_registry import execute_formula,FormulaError,public_catalog,load_registry


def calc(method,**kwargs):
    return execute_formula(method,kwargs)['result']['value']


def test_registry_unique_statuses():
    methods=load_registry()
    assert len(methods)>=13
    assert all(x['status'] in ['tested_executor','catalog_only'] for x in methods.values())
    assert len(public_catalog('DSC'))>=5


def test_dsc_time_triangle_integral_and_mw_units():
    # 2 mW *10s/2 peak area=10 mJ; dividing by 2 mg =>5 J/g
    got=calc('dsc_enthalpy_time_v1',time_s=[0,5,10],heat_flow_mw=[0,2,0],baseline_mw=[0,0,0],sample_mass_mg=2)
    assert got==pytest.approx(5.0)


def test_dsc_temperature_integration_cooling_sign_is_time_orientation():
    args={'temperature_c':[100,90,80], 'heat_flow_mw':[0,-2,0], 'baseline_mw':[0,0,0],
          'scan_rate_k_min':10, 'sample_mass_mg':2}
    got=calc('dsc_enthalpy_temperature_v1',**args)
    # 20 K at 10 K/min =120s; triangle area -120 mJ /2mg=-60 J/g
    assert got==pytest.approx(-60.0)
    args['temperature_c']=[80,90,100]
    assert calc('dsc_enthalpy_temperature_v1',**args)==pytest.approx(-60.0)


def test_dsc_crystallinity_coldcrystallization_and_filler():
    r=calc('dsc_crystallinity_v1',melting_enthalpy_j_g=45,cold_crystallization_enthalpy_j_g=5,
         reference_enthalpy_j_g=100,filler_mass_fraction=0.2)
    assert r==pytest.approx(50)


def test_dsc_crystallinity_rejects_nonphysical_claim():
    with pytest.raises(FormulaError,match='>100%'):
        calc('dsc_crystallinity_v1',melting_enthalpy_j_g=120,cold_crystallization_enthalpy_j_g=0,
             reference_enthalpy_j_g=100,filler_mass_fraction=0)


def test_tga_mass_loss_and_first_crossing():
    assert calc('tga_mass_loss_v1',initial_mass_mg=10,final_mass_mg=8)==pytest.approx(20)
    out=calc('tga_t_at_loss_v1',temperature_c=[30,100,200,300],
         remaining_mass_percent=[100,99,95,80],mass_loss_target_percent=5)
    assert out==pytest.approx(200)


def test_tga_no_reached_threshold():
    with pytest.raises(FormulaError,match='not reached'):
        calc('tga_t_at_loss_v1',temperature_c=[30,100,200],remaining_mass_percent=[100,99,98],
             mass_loss_target_percent=5)


def test_uvvis_and_ftir():
    assert calc('uv_beer_lambert_v1',absorbance=0.4,epsilon_l_mol_cm=1000,path_length_cm=1)==pytest.approx(.0004)
    assert calc('ftir_transmittance_v1',transmittance_fraction=.1)==pytest.approx(1.0)
    with pytest.raises(FormulaError):
        calc('ftir_transmittance_v1',transmittance_fraction=80)


def test_gpc_moments_using_actual_mass_fractions():
    obj=calc('gpc_mass_moments_v1',molar_mass_g_mol=[10000,20000],mass_fraction=[.25,.75])
    assert obj['Mn_g_mol']==pytest.approx(16000)
    assert obj['Mw_g_mol']==pytest.approx(17500)
    assert obj['dispersity']==pytest.approx(1.09375)
    with pytest.raises(FormulaError,match='must already sum to 1'):
        calc('gpc_mass_moments_v1',molar_mass_g_mol=[10000,20000],mass_fraction=[.25,.50])


def test_nmr_integral_ratio():
    assert calc('nmr_integral_ratio_v1',integral_a=6,integral_b=4,protons_a=3,protons_b=2)==pytest.approx(1.0)


def test_hallucinated_and_catalog_only_methods_blocked():
    with pytest.raises(FormulaError,match='Unknown method'):
        execute_formula('evil_python_formula',{})
    with pytest.raises(FormulaError,match='not executable'):
        execute_formula('dsc_tg_midpoint_v1',{})
    with pytest.raises(FormulaError,match='Input keys mismatch'):
        execute_formula('ftir_transmittance_v1',{'transmittance_fraction':.5,'code':'eval'} )


def test_nan_and_boolean_rejected():
    with pytest.raises(FormulaError):
        calc('uv_beer_lambert_v1',absorbance=True,epsilon_l_mol_cm=1000,path_length_cm=1)
    with pytest.raises(FormulaError):
        calc('uv_beer_lambert_v1',absorbance=float('nan'),epsilon_l_mol_cm=1000,path_length_cm=1)
