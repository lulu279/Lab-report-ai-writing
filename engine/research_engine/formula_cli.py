"""List and execute reviewed formulas. Examples in docs. Run via `python -m research_engine.formula_cli`."""
from __future__ import annotations
import argparse, json
from pathlib import Path
from .formula_registry import public_catalog,execute_formula,FormulaError


def main():
    parser = argparse.ArgumentParser(description='Scientific formula registry (validated local executors)')
    sub = parser.add_subparsers(dest='command',required=True)
    p_list=sub.add_parser('list',help='list available methods'); p_list.add_argument('--experiment',default=None)
    p_show=sub.add_parser('show',help='show one method');p_show.add_argument('method_id')
    p_run=sub.add_parser('run',help='execute one reviewed method');p_run.add_argument('method_id');p_run.add_argument('input_json')
    args=parser.parse_args()
    if args.command=='list':
        for m in public_catalog(args.experiment):
            print(f"{m['id']:<36} {m['status']:<18} {m['title_zh']}")
    elif args.command=='show':
        matches=[m for m in public_catalog() if m['id']==args.method_id]
        if not matches:raise SystemExit('Unknown method ID')
        print(json.dumps(matches[0],ensure_ascii=False,indent=2))
    elif args.command=='run':
        try:
            args_obj=json.loads(Path(args.input_json).read_text(encoding='utf-8'))
            print(json.dumps(execute_formula(args.method_id,args_obj),ensure_ascii=False,indent=2))
        except (FormulaError,ValueError) as exc:
            raise SystemExit(f'Formula rejected: {exc}')

if __name__=='__main__':
    main()
