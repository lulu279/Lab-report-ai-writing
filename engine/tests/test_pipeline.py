import json
from pathlib import Path
from docx import Document
from research_engine.pipeline import run, pack_outputs

ROOT=Path(__file__).resolve().parents[1]

def test_entire_pipeline_outputs_unreviewed_draft(tmp_path):
    work=run(ROOT/'examples'/'synthetic_dsc.csv',ROOT/'examples'/'synthetic_config.json',tmp_path)
    assert (work/'manifest.json').exists()
    assert (work/'results.json').exists()
    assert (work/'validation.json').exists()
    assert (work/'report_draft.docx').exists()
    assert len(list((work/'figures').glob('*.svg')))>=2
    result=json.loads((work/'results.json').read_text(encoding='utf-8'))
    manifest=json.loads((work/'manifest.json').read_text(encoding='utf-8'))
    assert result['data_sha256']==manifest['data_sha256']
    assert manifest['source_example_results_used'] is False
    d=Document(work/'report_draft.docx')
    text='\n'.join(p.text for p in d.paragraphs)
    assert '合成测试数据' in text
    assert '待人工审核' in text
    assert pack_outputs(work).exists()


def test_failed_numeric_qc_blocks_docx(tmp_path):
    src=json.loads((ROOT/'examples'/'synthetic_config.json').read_text(encoding='utf-8'))
    src['samples'][0]['endotherm_up']=False
    bad_cfg=tmp_path/'sign_error.json'
    bad_cfg.write_text(json.dumps(src,ensure_ascii=False),encoding='utf-8')
    output=run(ROOT/'examples'/'synthetic_dsc.csv',bad_cfg,tmp_path/'runs')
    assert (output/'results.json').exists()
    assert (output/'validation.json').exists()
    assert not (output/'report_draft.docx').exists()
    assert json.loads((output/'run_log.json').read_text())['status']=='BLOCKED_NUMERICAL_QA'
