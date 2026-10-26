import argparse
from pathlib import Path
from .pipeline import run,pack_outputs


def main():
    p=argparse.ArgumentParser(description='DSC report prototype - validated CSV+config required')
    p.add_argument('--data',required=True,type=Path,help='Normalized CSV')
    p.add_argument('--config',required=True,type=Path,help='YAML/JSON with explicit units/mass/windows')
    p.add_argument('--out',type=Path,default=Path('runs'))
    p.add_argument('--ai',action='store_true',help='Use optional API to generate UNREVIEWED discussion only')
    p.add_argument('--model',default=None,help='Required with --ai; use an accessible API model ID')
    args=p.parse_args()
    if args.ai and not args.model:
        p.error('--model must be set with --ai')
    folder=run(args.data,args.config,args.out,use_ai=args.ai,model=args.model)
    bundle=pack_outputs(folder)
    print(f'RUN_DIR: {folder.resolve()}')
    print(f'OUTPUT_BUNDLE: {bundle.resolve()}')
    print(f'Check validation.json and run_log.json before using a report.')


if __name__=='__main__':
    main()
