"""Launch using: streamlit run app.py"""
from __future__ import annotations
import json
import tempfile
from pathlib import Path
import streamlit as st
from research_engine.pipeline import run,pack_outputs

st.set_page_config(page_title='Research DSC Engine',layout='wide')
st.title('DSC 科研数据与报告工作台 · MVP')
st.caption('仅支持显式分段的标准化 UTF-8 CSV。输入为合成数据时必须保留 SYNTHETIC 标识。')
st.warning('这是辅助数据分析与报告草稿工具，不是已通过科研审核的自动投稿/作业生成系统。')

with st.expander('输入格式说明（首次使用必读）',expanded=False):
    st.code('sample_id,segment,time_s,temperature_c,heat_flow_mw\nPE,H1,0,25.0,2.1\nPE,H1,1,25.25,2.1')
    st.markdown('配置文件需声明样品质量 mg、吸热方向、积分窗口、数据类型和单位。程序不会猜测仪器导出列名或自动识别扫描阶段。')
    st.markdown('预置演示位于 `examples/`，是**合成数据**，并非上传的 DSC 实验原始结果。')

left,right=st.columns(2)
with left:
    data=st.file_uploader('1. 上传标准化 CSV',type=['csv'])
with right:
    config=st.file_uploader('2. 上传 JSON/YAML 配置',type=['json','yaml','yml'])
use_ai=st.checkbox('使用 AI 写一段讨论草稿（仅当已设置 OPENAI_API_KEY）',value=False)
model=st.text_input('API 模型 ID（由你自行填写可用模型）',value='',disabled=not use_ai)
with st.expander('首次运行建议'):
    st.markdown('先上传 examples/synthetic_dsc.csv 与 examples/synthetic_config.json，验证程序运行后，再准备真实实验的标准化 CSV 和配置。')

if st.button('运行数据分析并生成 DOCX 草稿',type='primary',disabled=not(data and config)):
    with st.spinner('执行输入验证、积分、绘图、文档生成和数值质量检查'):
        with tempfile.TemporaryDirectory(prefix='dsc_upload_') as td:
            td=Path(td)
            dp=td/'upload.csv'
            suffix=Path(config.name).suffix.lower()
            cp=td/('upload'+suffix)
            if len(data.getvalue())>30*1024*1024 or len(config.getvalue())>1024*1024:
                st.error('CSV 最大 30MB；配置最大 1MB。请分批处理。')
                st.stop()
            dp.write_bytes(data.getvalue()); cp.write_bytes(config.getvalue())
            try:
                result_dir=run(dp,cp,Path('runs'),use_ai=use_ai,model=model.strip() or None)
                info=json.loads((result_dir/'validation.json').read_text(encoding='utf-8'))
                st.write('运行目录：',str(result_dir))
                st.write('数值状态：',info['numerical_status'])
                st.write('科学审查：',info['scientific_interpretation_status'])
                st.dataframe(info['issues'],use_container_width=True)
                if (result_dir/'results.json').exists():
                    values=json.loads((result_dir/'results.json').read_text(encoding='utf-8'))
                    st.dataframe(values['events'],use_container_width=True)
                if info['numerical_status']=='FAIL':
                    st.error('数值检查失败：停止生成正式报告，仅保留证据与错误记录。')
                else:
                    st.success('已生成可编辑的 DOCX 草稿；仍需人工科学/版式审核。')
                package=pack_outputs(result_dir)
                st.download_button('下载本次完整输出 ZIP',data=package.read_bytes(),
                                   file_name=package.name,mime='application/zip')
                if (result_dir/'report_draft.docx').exists():
                    st.download_button('单独下载 Word 草稿',
                                       data=(result_dir/'report_draft.docx').read_bytes(),
                                       file_name='report_draft.docx',
                                       mime='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
            except Exception as exc:
                st.error(f'{type(exc).__name__}: {exc}')
                st.info('未生成报告。请核查上传数据的列名、单位、阶段与积分配置。')

st.divider()
st.header('实验分析方法规划器 · AI 建议 + 人工确认（v0.2）')
st.info('当前只支持 DSC。AI 可建议事件类型、积分区间与两种已实现基线法，不能运行任意生成的代码。此功能只有点击按钮且配置 API Key 后才会向外部模型发送数据概况。')
st.caption('规划用配置可以省略 windows，但必须提供实际样品质量、热流方向、数据类型与单位。')
with st.expander('支持的方法与隐私说明'):
    st.markdown('- `dsc_peak_area_time_v1`：扣除基线后对时间积分，再除样品质量，支持熔融、降温结晶、升温冷结晶。\n- 可选择 `linear_endpoint_mean` 或 `constant_endpoint_mean` 基线；会独立运行敏感度和符号检查。\n- `dsc_tg_midpoint_v1` 尚未实现：只能列为待人工分析。\n- 只向配置的外部 AI 服务发送样品配置、段落统计和每段最多 32 个均值采样点；不会默认发送完整 CSV。')
model_plan=st.text_input('模型 ID（例如你有权限使用的某个 API 模型）',value='',key='plan_model')
endpoint=st.text_input('兼容 OpenAI 协议的 API Base URL（可留空使用官方默认）',value='',key='plan_endpoint')

def _uploaded_paths(directory):
    dp=directory/'uploaded.csv'
    cp=directory/('metadata'+Path(config.name).suffix.lower())
    dp.write_bytes(data.getvalue())
    cp.write_bytes(config.getvalue())
    return dp,cp

import hashlib
fingerprint=(hashlib.sha256(data.getvalue()+config.getvalue()).hexdigest() if (data and config) else None)
if st.button('① 让真实 AI 提议分析方法（需要 API Key）',disabled=not(data and config and model_plan.strip())):
    if len(data.getvalue())>30*1024*1024 or len(config.getvalue())>1024*1024:
        st.error('文件体积超过限制：CSV 30MB、配置 1MB')
    else:
        with st.spinner('从数据中生成摘要，调用指定模型，校验其建议……'):
            try:
                from research_engine.planner import preview_ai_plan
                with tempfile.TemporaryDirectory(prefix='dsc_plan_') as td:
                    dp,cp=_uploaded_paths(Path(td))
                    plan_preview=preview_ai_plan(dp,cp,model=model_plan.strip(),base_url=endpoint.strip() or None)
                st.session_state['ai_plan_preview']=plan_preview
                st.session_state['ai_plan_fingerprint']=fingerprint
                st.success('模型已给出方案并通过基础结构检查。尚未执行计算。')
            except Exception as exc:
                st.session_state.pop('ai_plan_preview',None)
                st.error(f'规划失败：{type(exc).__name__}：{exc}')

current_preview=st.session_state.get('ai_plan_preview')
if current_preview and st.session_state.get('ai_plan_fingerprint')==fingerprint:
    st.subheader('② 审核 AI 的方法与公式选择')
    st.warning('以下内容仍是模型建议，不是经过验证的科学结论。请核对每个峰所属阶段、积分范围、基线是否合适。')
    st.json(current_preview['proposal'])
    if current_preview['local_warnings']:
        st.warning('本地检查提示（低模型置信度、未覆盖阶段等）：')
        st.dataframe(current_preview['local_warnings'],use_container_width=True)
    st.download_button('下载 AI 建议的分析配置（JSON）',data=json.dumps(current_preview['candidate_config'],ensure_ascii=False,indent=2),file_name='ai_suggested_config.json',mime='application/json')
    st.caption('若需要调整方法/积分区间，下载配置并修改，使用上方标准流程运行；这一步不应视为已经批准 AI 建议。')
    approval=st.checkbox('我已检查本次建议的积分区间、峰类型、基线方法和必要的样品元数据，并同意执行该方案',value=False,key='approve_ai_plan')
    if st.button('③ 确认并执行 AI 建议（输出带溯源记录）',disabled=not approval,type='primary'):
        try:
            from research_engine.planner import load_planning_inputs,validate_ai_plan
            with tempfile.TemporaryDirectory(prefix='dsc_plan_execute_') as td:
                tmp=Path(td)
                dp,cp=_uploaded_paths(tmp)
                df,raw=load_planning_inputs(dp,cp)
                # Validate the exact plan against the uploaded inputs a second time.
                cfg,warnings=validate_ai_plan(current_preview['proposal'],df,raw)
                cfg_path=tmp/'accepted_analysis_config.json'
                cfg_path.write_text(json.dumps(cfg,ensure_ascii=False,indent=2),encoding='utf-8')
                plan_path=tmp/'approved_ai_plan.json'
                record={**current_preview, 'human_approved':True, 'approved_config_sha256':hashlib.sha256(cfg_path.read_bytes()).hexdigest()}
                plan_path.write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
                work=run(dp,cfg_path,Path('runs'),analysis_plan_path=plan_path)
                qa=json.loads((work/'validation.json').read_text(encoding='utf-8'))
                st.write('本次计算状态：',qa['numerical_status'])
                st.dataframe(qa['issues'],use_container_width=True)
                if qa['numerical_status']=='FAIL':
                    st.error('独立数值验收失败，已停止生成 Word 草稿。')
                else:
                    st.success('程序已完成数值计算和文档草稿；科学解释仍需人工审阅。')
                bundle=pack_outputs(work)
                st.download_button('下载包含 AI 方法溯源的全部运行记录',data=bundle.read_bytes(),file_name='AI_DSC_run.zip',mime='application/zip')
        except Exception as exc:
            st.error(f'运行失败：{type(exc).__name__}：{exc}')

st.divider()
st.header('科学公式注册库（v0.3）')
st.caption('独立于 DSC 报告流水线的公式查阅与受控计算。可执行 ≠ 已针对你的真实实验完成科学审核。')
from research_engine.formula_registry import public_catalog,execute_formula,FormulaError
catalog=public_catalog()
choose=st.selectbox('选择需要查阅或计算的方法',options=[m['id'] for m in catalog],
                    format_func=lambda id: next(x['title_zh'] for x in catalog if x['id']==id))
chosen=next(x for x in catalog if x['id']==choose)
st.markdown('**表达式：** '+chosen['equation'])
st.write('状态：', '已有基础数值测试（仍需实验验证）' if chosen['status']=='tested_executor' else '待开发：不能执行')
st.write('输入变量及要求：',chosen['inputs'])
with st.expander('物理前提、资料和限制'):
    st.write(chosen['assumptions']);st.caption(chosen['reference']);st.write(chosen.get('notes',''))
if chosen['status']=='tested_executor':
    st.warning('仅用于单次受控公式演示，不会将这里的演示数值写进 DSC 报告。真实数据的适用性仍需独立确认。')
    request=st.text_area('输入 JSON 参数（字段必须精确匹配）',value=json.dumps({x:None for x in chosen['inputs']},ensure_ascii=False,indent=2),height=180)
    if st.button('执行当前已验证公式'):
        try:
            result=execute_formula(choose,json.loads(request))
            st.json(result)
        except Exception as exc:
            st.error(str(exc))
else:
    st.info('该方法只有信息卡，不存在可执行函数；需独立实现、测试并审核后才能开放。')
