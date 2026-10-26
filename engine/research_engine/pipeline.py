"""Reproducible local pipeline with immutable inputs and honest quality flags."""
from __future__ import annotations
import datetime as dt
import hashlib
import json
import shutil
import uuid
import zipfile
from pathlib import Path
import yaml
from .schema import parse_config, InputError
from .loader import parse_csv
from .calculations import analyze
from .figures import create_figures
from .report import build_docx


def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):
            h.update(block)
    return h.hexdigest()


def _write_json(path: Path, content: dict):
    path.write_text(json.dumps(content,ensure_ascii=False,indent=2),encoding='utf-8')


def load_config(path: Path) -> dict:
    if path.suffix.lower() in ['.yml','.yaml']:
        return yaml.safe_load(path.read_text(encoding='utf-8-sig'))
    if path.suffix.lower()=='.json':
        return json.loads(path.read_text(encoding='utf-8-sig'))
    raise InputError("Config must be .json, .yml or .yaml")


def run(data_path: Path, config_path: Path, run_root: Path, use_ai=False,
        model=None, knowledge_path=None, analysis_plan_path=None) -> Path:
    data_path,config_path,run_root=Path(data_path),Path(config_path),Path(run_root)
    config_raw=load_config(config_path)
    config=parse_config(config_raw)
    run_id=dt.datetime.now().strftime('%Y%m%d_%H%M%S')+'_'+uuid.uuid4().hex[:8]
    work=run_root/run_id
    inp=work/'inputs'
    inp.mkdir(parents=True)
    data_saved=inp/'data.csv'
    cfg_saved=inp/('config'+config_path.suffix.lower())
    shutil.copyfile(data_path,data_saved)
    shutil.copyfile(config_path,cfg_saved)
    plan_sha = None
    if analysis_plan_path is not None:
        analysis_plan_path = Path(analysis_plan_path)
        if not analysis_plan_path.exists():
            raise InputError("AI plan provenance file is missing")
        shutil.copyfile(analysis_plan_path, inp/'ai_plan.json')
        plan_sha = sha256(inp/'ai_plan.json')
    manifest={
        'run_id':run_id,'engine_version':'0.2.0','created_at':dt.datetime.now(dt.timezone.utc).isoformat(),
        'dataset_type':config.dataset_type,'data_sha256':sha256(data_saved),
        'config_sha256':sha256(cfg_saved),'data_units':config.measurement_units,
        'source_example_results_used':False,'ai_requested':bool(use_ai),
        'raw_csv':'inputs/data.csv','metadata_file':'inputs/'+cfg_saved.name,
        'model_id':model if use_ai else None,
        'baseline_fraction':config.baseline_fraction,
        'analysis_plan_sha256':plan_sha,
        'analysis_plan_status':'HUMAN_APPROVED' if plan_sha else 'NOT_USED',
    }
    _write_json(work/'manifest.json',manifest)
    try:
        df=parse_csv(data_saved,config)
        events, issues, bundle=analyze(df,config)
        qa=bundle['qc']
        results={
            'schema_version':'0.1','run_id':run_id,'dataset_type':config.dataset_type,
            'data_sha256':manifest['data_sha256'],'events':events,'validation':qa
        }
        _write_json(work/'results.json', results)
        _write_json(work/'validation.json',qa)
        if qa['numerical_status']=='FAIL':
            _write_json(work/'run_log.json',{'status':'BLOCKED_NUMERICAL_QA', 'reasons':qa['issues']})
            return work
        figure_files=create_figures(df,bundle['curves'],config,work/'figures')
        results['figures']=figure_files
        _write_json(work/'results.json',results)
        discussion=None
        if use_ai:
            from .ai import generate_discussion
            if knowledge_path is None:
                knowledge_path=Path(__file__).resolve().parents[1]/'knowledge'/'ACTIVE_STYLE.md'
            try:
                discussion=generate_discussion(results,config,Path(knowledge_path),model)
                (work/'ai_discussion_draft.txt').write_text(discussion,encoding='utf-8')
            except Exception as exc:
                # Do not misrepresent a failed AI step as AI-generated content.
                qa['issues'].append({'severity':'WARN','code':'AI_UNAVAILABLE',
                                    'event_id':None,'message':str(exc)})
                qa['ai_status']='FAILED'
                qa['numerical_status']='WARN' if qa['numerical_status']=='PASS' else qa['numerical_status']
                _write_json(work/'validation.json',qa)
                _write_json(work/'results.json',results)
        qa['ai_status']=('DRAFT_UNREVIEWED' if discussion else qa.get('ai_status','NOT_USED'))
        build_docx(work/'report_draft.docx',results,config,work/'figures',discussion)
        _write_json(work/'validation.json',qa)
        _write_json(work/'results.json',results)
        _write_json(work/'run_log.json',{
            'status':'DRAFT_CREATED_HUMAN_REVIEW_REQUIRED',
            'next_actions':['verify source/calibration','scientific interpretation review',
                            'render DOCX on target system and visually inspect','confirm school AI policy'],
        })
        return work
    except Exception as exc:
        _write_json(work/'run_log.json',{'status':'INPUT_OR_PIPELINE_ERROR','error':str(exc),
                                        'error_type':type(exc).__name__})
        raise


def pack_outputs(run_dir: Path) -> Path:
    output=run_dir/'download_bundle.zip'
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as z:
        for f in run_dir.rglob('*'):
            if f.is_file() and f != output:
                z.write(f,f.relative_to(run_dir))
    return output
