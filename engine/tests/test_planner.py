"""Offline tests inject simulated model JSON; no real API calls or model quality claims."""
import copy
import json
from pathlib import Path
import pytest
from research_engine.planner import (load_planning_inputs,data_profile,validate_ai_plan,_strip_json)
from research_engine.schema import InputError,parse_config
from research_engine.loader import parse_csv
from research_engine.calculations import analyze
from research_engine.pipeline import run

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'examples/synthetic_dsc.csv'
CONFIG=ROOT/'examples/synthetic_config.json'


def fake_ai_response():
    # Use an offline fixture to verify the interface, not as evidence of LLM autonomous performance.
    cfg=json.loads(CONFIG.read_text(encoding='utf8'))
    events=[dict(win, method_id='dsc_peak_area_time_v1', baseline_method='linear_endpoint_mean',
                 confidence=0.92,reason='Gaussian-like event on a monotonic DSC scan, with baseline on both sides.',
                 evidence='Segment has a localized deflection across the proposed integration range.') for win in cfg['windows']]
    return {'plan_version':'0.2','experiment_type':'DSC','baseline_fraction':0.1,
            'events':events,'deferred_events':[], 'questions_for_user':[], 'general_limitations':[]}


def test_no_window_config_can_be_profiled():
    df,cfg=load_planning_inputs(DATA,CONFIG)
    cfg.pop('windows')
    parsed=parse_config(dict(cfg,windows=[]), require_windows=False)
    assert not parsed.windows
    prof=data_profile(df,cfg)
    assert prof['raw_data_sent'] is False
    assert len(prof['segments'])==8
    assert all(len(s['temperature_heat_flow_preview'])<=32 for s in prof['segments'])


def test_valid_plan_generates_computable_config():
    df,raw=load_planning_inputs(DATA,CONFIG)
    candidate,warns=validate_ai_plan(fake_ai_response(),df,raw)
    assert not warns
    arr,_,quality=analyze(df,parse_config(candidate))
    assert quality['qc']['numerical_status']!='FAIL'
    assert len(arr)==8


def test_reject_hallucinated_event_or_formula():
    df,raw=load_planning_inputs(DATA,CONFIG)
    plan=fake_ai_response()
    plan['events'][0]['method_id']='unknown_magic_formula'
    with pytest.raises(InputError,match='Unsupported algorithm'):
        validate_ai_plan(plan,df,raw)
    plan=fake_ai_response()
    plan['events'][0]['sample_id']='hallucinated'
    with pytest.raises(InputError,match='Hallucinated'):
        validate_ai_plan(plan,df,raw)


def test_reject_window_outside_segment():
    df,raw=load_planning_inputs(DATA,CONFIG)
    plan=fake_ai_response()
    plan['events'][0]['start_c']=-1000
    with pytest.raises(InputError,match='outside recorded'):
        validate_ai_plan(plan,df,raw)


def test_explicit_review_for_uncovered_segment():
    df,raw=load_planning_inputs(DATA,CONFIG)
    plan=fake_ai_response()
    plan['events']=plan['events'][:1]
    cfg,warns=validate_ai_plan(plan,df,raw)
    assert len(cfg['windows'])==1
    assert any(w['code']=='UNCOVERED_SEGMENT' for w in warns)


def test_constant_endpoint_baseline_is_supported():
    df,raw=load_planning_inputs(DATA,CONFIG)
    plan=fake_ai_response()
    plan['events'][0]['baseline_method']='constant_endpoint_mean'
    cfg,warns=validate_ai_plan(plan,df,raw)
    assert cfg['windows'][0]['baseline_method']=='constant_endpoint_mean'
    outputs,_,qa=analyze(df,parse_config(cfg))
    assert outputs[0]['method'].startswith('constant_endpoint_mean')


def test_executed_plan_is_hash_logged(tmp_path):
    df,raw=load_planning_inputs(DATA,CONFIG)
    candidate,_=validate_ai_plan(fake_ai_response(),df,raw)
    cfg=tmp_path/'approved.json';cfg.write_text(json.dumps(candidate),encoding='utf-8')
    plan=tmp_path/'plan.json';plan.write_text(json.dumps({'model_requested':'offline_fake','human_approved':True}),encoding='utf8')
    work=run(DATA,cfg,tmp_path/'runs',analysis_plan_path=plan)
    meta=json.loads((work/'manifest.json').read_text(encoding='utf8'))
    assert meta['analysis_plan_sha256']
    assert meta['analysis_plan_status']=='HUMAN_APPROVED'
    assert (work/'inputs/ai_plan.json').exists()
    assert (work/'report_draft.docx').exists()


def test_invalid_model_json_refused():
    with pytest.raises(json.JSONDecodeError):
        _strip_json('{not a json}')
