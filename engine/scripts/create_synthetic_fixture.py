"""Generate deterministic synthetic DSC scans for tests ONLY. No user report values used."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd


def generate(out: Path):
    out.mkdir(parents=True,exist_ok=True)
    series=[]
    config={
        'dataset_type':'synthetic',
        'dataset_label':'DEMO ONLY | Synthetic PE/PET scans',
        'measurement_units':{'time_s':'s','temperature_c':'degC','heat_flow_mw':'mW'},
        'baseline_fraction':0.1,
        'samples':[], 'windows':[],
    }
    definitions=[
        ('PE_demo','PE',5.0,25.,150.,15.,[(102.,4.5,3.),(86.,-4.,3.),(104.,5.0,3.5),(89.,-4.5,3.)]),
        ('PET_demo','PET',3.6,25.,265.,10.,[(232.,4.0,5.),(196.,-3.3,4.),(234.,4.2,5.),(198.,-3.7,4.)]),
    ]
    for sid,poly,mass,tmin,tmax,rate,peaks in definitions:
        config['samples'].append({
            'sample_id':sid,'polymer':poly,'mass_mg':mass,'endotherm_up':True,
            'delta_h0_j_g':293.0 if poly=='PE' else 140.0,
            'delta_h0_reference':'User reference report; NOT independently verified',
            'reference_verified':False,
            'cold_crystallization_excluded':True,
        })
        t=0.
        for idx,(loc,amp,sigma) in enumerate(peaks):
            phase='melting' if idx%2==0 else 'crystallization'
            segment=('H' if idx%2==0 else 'C')+str(idx//2+1)
            n=1001
            temp=np.linspace(tmin,tmax,n) if phase=='melting' else np.linspace(tmax,tmin,n)
            step=(tmax-tmin)/rate*60/(n-1)
            tt=t+np.arange(n)*step
            flux=2.0+0.001*tt+amp*np.exp(-.5*((temp-loc)/sigma)**2)
            for ti,ci,hi in zip(tt,temp,flux):
                series.append({'sample_id':sid,'segment':segment,'time_s':float(ti),
                               'temperature_c':float(ci),'heat_flow_mw':float(hi)})
            t=float(tt[-1])+120.
            # Windows selected strictly within each scan and visibly enclose one generated Gaussian.
            lower=max(tmin,loc-9*sigma)
            upper=min(tmax,loc+9*sigma)
            config['windows'].append({'event_id':f'{sid}_{segment}_{phase}',
                                      'sample_id':sid,'segment':segment,'phase':phase,
                                      'start_c':float(lower),'end_c':float(upper)})
    pd.DataFrame(series).to_csv(out/'synthetic_dsc.csv',index=False)
    (out/'synthetic_config.json').write_text(json.dumps(config,ensure_ascii=False,indent=2),encoding='utf-8')
    return out


if __name__=='__main__':
    print(generate(Path(__file__).resolve().parents[1]/'examples'))
