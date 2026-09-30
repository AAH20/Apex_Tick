"""Icarus scoreboard against an independently expressed dictionary oracle."""
import json
import random
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from apex_tick.oracle import Oracle, stimulus
FIELDS=('recover','terminal_valid','terminal_id','valid','frame_ok','seq','instrument','price','qty','epoch','limit','rate_limit','out_ready')


def cases(seed=17,cycles=800):
    rng=random.Random(seed);model=Oracle();events=[];expected=[]
    for i in range(cycles):
        if model.hold and model.exposure==0:
            event=stimulus(recover=1,epoch=model.epoch+1,seq=model.expected,limit=rng.choice([2,8,16]),rate_limit=rng.choice([1,4,16]))
        elif model.pending and rng.random()<.3:
            event=stimulus(terminal_valid=1,terminal_id=rng.choice(list(model.pending)),epoch=model.epoch)
        else:
            event=stimulus(valid=1,seq=model.expected,epoch=model.epoch,price=rng.choice([99,100,101]),qty=rng.choice([1,2]),instrument=rng.randrange(8),out_ready=int(rng.random()>.2))
            fault=rng.randrange(15)
            if fault==0:event['frame_ok']=0
            elif fault==1:event['seq']=max(0,model.expected-1)
            elif fault==2:event['seq']=model.expected+1
            elif fault==3:event['instrument']=8
            elif fault==4:event['epoch']=max(0,model.epoch-1)
        events.append(event);expected.append(model.step(event))
    return events,expected


def verify(seed=17,cycles=800):
    if not shutil.which('iverilog') or not shutil.which('vvp'):
        raise RuntimeError('Icarus Verilog is required; verification cannot silently skip')
    events,expected=cases(seed,cycles)
    with tempfile.TemporaryDirectory() as temp:
        directory=Path(temp);inputs=directory/'input.txt';output=directory/'output.txt';binary=directory/'core.vvp'
        inputs.write_text(''.join(' '.join(str(e[f]) for f in FIELDS)+'\n' for e in events))
        subprocess.run(['iverilog','-g2012','-s','core_tb','-o',str(binary),str(ROOT/'rtl/apex_tick_core.sv'),str(ROOT/'verification/core_tb.sv')],check=True)
        subprocess.run(['vvp',str(binary),f'+input={inputs}',f'+output={output}'],check=True,capture_output=True,text=True)
        rows=[[int(x) for x in line.split()] for line in output.read_text().splitlines()]
    if len(rows)!=len(expected):raise AssertionError('RTL trace length mismatch')
    for i,(row,want) in enumerate(zip(rows,expected)):
        actual=dict(ready=row[0],out_valid=row[1],order=tuple(row[2:6]),hold=row[6],exposure=row[7],expected=row[8],status=row[9])
        if actual!=want:raise AssertionError(f'cycle {i}: RTL {actual}; oracle {want}; stimulus {events[i]}')
    return {'environment':'rtl_simulation','seed':seed,'cycles':cycles,'matching_transitions':len(rows),'physical_latency_ns':None,'status':'passed','trace':rows}


if __name__=='__main__':
    result=verify();result.pop('trace');print(json.dumps(result,indent=2))
