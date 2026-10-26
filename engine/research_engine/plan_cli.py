"""Optional real AI method planning CLI. Planning does not calculate or produce a report."""
import argparse
import json
from pathlib import Path
from .planner import preview_ai_plan


def main():
    p=argparse.ArgumentParser(description='Obtain and validate a DSC method plan from an external model')
    p.add_argument('--data',type=Path,required=True)
    p.add_argument('--config',type=Path,required=True)
    p.add_argument('--model',required=True)
    p.add_argument('--base-url',default=None)
    p.add_argument('--out',type=Path,default=Path('ai_plan_preview.json'))
    a=p.parse_args()
    payload=preview_ai_plan(a.data,a.config,model=a.model,base_url=a.base_url)
    a.out.write_text(json.dumps(payload,indent=2,ensure_ascii=False),encoding='utf-8')
    candidate=a.out.with_name(a.out.stem+'_suggested_config.json')
    candidate.write_text(json.dumps(payload['candidate_config'],indent=2,ensure_ascii=False),encoding='utf-8')
    print(f'Plan proposal stored: {a.out}')
    print(f'Suggested config stored: {candidate}')
    print('WARNING: Model advice has not been executed or approved. Inspect the plan before running the normal CLI.')

if __name__=='__main__':
    main()
