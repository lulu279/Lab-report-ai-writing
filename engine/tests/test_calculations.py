import copy
import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from research_engine.schema import parse_config, InputError
from research_engine.loader import parse_csv
from research_engine.calculations import analyze

ROOT=Path(__file__).resolve().parents[1]
CONFIG=json.loads((ROOT/'examples'/'synthetic_config.json').read_text(encoding='utf-8'))
DATA=ROOT/'examples'/'synthetic_dsc.csv'


def test_fixture_synthetic_and_source_isolation():
    cfg=parse_config(CONFIG)
    df=parse_csv(DATA,cfg)
    values,_,out=analyze(df,cfg)
    assert len(values)==8
    assert all(v['integrated_area_mj_endotherm_up']>0 for v in values if v['phase']=='melting')
    assert all(v['integrated_area_mj_endotherm_up']<0 for v in values if v['phase']=='crystallization')
    assert out['qc']['numerical_status']!='FAIL'
    assert out['qc']['scientific_interpretation_status']=='NOT_REVIEWED'
    assert any(x['code']=='SYNTHETIC_DATA' for x in out['qc']['issues'])


def test_integral_uses_time_and_has_analytic_limit():
    # Independent analytical expectation for a Gaussian peak: area=A*sigma_t*sqrt(2π).
    cfg=copy.deepcopy(CONFIG)
    cfg['samples']=[dict(cfg['samples'][0],sample_id='trial',mass_mg=5.,delta_h0_j_g=None)]
    cfg['windows']=[{'event_id':'trial_peak','sample_id':'trial',
                     'segment':'H1','phase':'melting','start_c':0.,'end_c':100.}]
    cfg=parse_config(cfg)
    times=np.linspace(0.,1000.,2001)
    temp=np.linspace(0.,100.,len(times))
    flux=6.*np.exp(-0.5*((times-500.)/35.)**2)
    df=pd.DataFrame({'sample_id':'trial','segment':'H1','time_s':times,
                     'temperature_c':temp,'heat_flow_mw':flux})
    out,_,qa=analyze(df,cfg)
    expected=6*35*np.sqrt(2*np.pi)/5.  # mJ / mg = J/g
    assert out[0]['enthalpy_j_g']==pytest.approx(expected,rel=0.002)
    assert qa['qc']['numerical_status']!='FAIL'


def test_missing_units_fail_closed():
    cfg=copy.deepcopy(CONFIG)
    cfg['measurement_units']['heat_flow_mw']='W/g'
    with pytest.raises(InputError): parse_config(cfg)


def test_wrong_heat_flow_sign_blocks_results():
    cfg=copy.deepcopy(CONFIG)
    cfg['samples'][0]['endotherm_up']=False
    cfg=parse_config(cfg)
    df=parse_csv(DATA,cfg)
    _,_,out=analyze(df,cfg)
    assert out['qc']['numerical_status']=='FAIL'
    assert 'HEAT_FLOW_SIGN' in [x['code'] for x in out['qc']['issues']]


def test_missing_segment_fails(tmp_path):
    cfg=parse_config(CONFIG)
    df=pd.read_csv(DATA)
    df=df.drop(columns=['segment'])
    path=tmp_path/'broken.csv'; df.to_csv(path,index=False)
    with pytest.raises(InputError): parse_csv(path,cfg)


def test_no_auto_crystallinity_if_cold_crystallization_unknown():
    cfg=copy.deepcopy(CONFIG)
    cfg['samples'][0]['cold_crystallization_excluded']=None
    cfg=parse_config(cfg)
    df=parse_csv(DATA,cfg)
    values,_,_=analyze(df,cfg)
    pe_heating=[v for v in values if v['sample_id']=='PE_demo' and v['phase']=='melting']
    assert all(v['crystallinity_pct'] is None for v in pe_heating)


def test_narrow_integration_window_is_blocked():
    cfg=copy.deepcopy(CONFIG)
    # Peak is clipped and endpoint baseline becomes highly sensitive.
    cfg['windows'][0]['start_c']=98.0
    cfg['windows'][0]['end_c']=105.0
    obj=parse_config(cfg)
    df=parse_csv(DATA,obj)
    _,issues,info=analyze(df,obj)
    assert info['qc']['numerical_status']=='FAIL'
    assert any(x['code']=='BASELINE_UNSTABLE' for x in issues)
