"""Emit retained simulation evidence using the Atlas v0.1 contract."""
import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from verify import verify, ROOT


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--seed',type=int,default=17)
    parser.add_argument('--cycles',type=int,default=800)
    args=parser.parse_args()
    if args.cycles<=0 or args.cycles>1_000_000:parser.error('cycles must be within 1..1000000')
    if args.output.exists() and any(args.output.iterdir()):parser.error('output must be absent or empty')
    result=verify(args.seed,args.cycles)
    output=args.output;output.mkdir(parents=True,exist_ok=True)
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    dirty=bool(subprocess.check_output(['git','status','--porcelain','--untracked-files=no'],cwd=ROOT,text=True).strip())
    def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
    def dump(name,data):
        path=output/name;path.write_text(json.dumps(data,indent=2)+'\n');return path
    config={'seed':args.seed,'cycles':args.cycles,'instruments':8,'max_pending':16,'window_cycles':64}
    inventory={'environment':'Icarus RTL simulation','simulator_version':subprocess.check_output(['iverilog','-V'],text=True,stderr=subprocess.DEVNULL).splitlines()[0],'physical_board':None}
    build={'sources':{name:sha(ROOT/name) for name in ['rtl/apex_tick_core.sv','verification/core_tb.sv','verification/verify.py','src/apex_tick/oracle.py']}}
    spec=json.loads((ROOT/'spec/open-tick-v0.json').read_text())
    artifacts=[]
    for name,role,value in [('config.json','configuration',config),('inventory.json','platform_inventory',inventory),('build.json','implementation',build),('workload.json','workload',spec),('input.json','stimulus_seed_and_bound',config),('trace.json','cycle_transition_trace',result['trace'])]:
        path=dump(name,value);artifacts.append({'id':name[:-5],'role':role,'location':name,'sha256':sha(path),'visibility':'public'})
    record={'schema_version':'0.1.0','run_id':f'apex-tick-simulation-{args.seed}-{args.cycles}','status':'valid','claim_kind':'measured',
        'provenance':{'repository_url':'https://github.com/AAH20/Apex_Tick','commit':commit,'dirty':dirty,'config_sha256':sha(output/'config.json'),'recorded_at':datetime.now(timezone.utc).isoformat(),'sources':[]},
        'workload':{'id':'apex.tick.core.functional','version':'0.1.0','kind':'synthetic','spec_sha256':sha(output/'workload.json'),'input_sha256':sha(output/'input.json'),'rights':'public_redistributable','semantics':'Seeded normalized-event stimulus cycles compared with independent dictionary oracle','frame_integrity_policy':'validate_before_action'},
        'platform':{'inventory_artifact':'inventory','implementation_artifact':'build','transport_backend':'normalized_event_testbench','backend_status':'simulated'},
        'evidence':{'implementation':'rtl_simulation','environment':'simulator','validation':'none','validation_receipt':None},
        'measurement':{'method':'simulation','start_boundary':'first normalized-event stimulus cycle','stop_boundary':'last scoreboard observation','clock_artifact':None,'calibration_artifact':None,'resolution_ns':None,'uncertainty_artifact':None,'warmup_policy':'none; functional verification','sampling_policy':'every stimulus cycle and registered output state','sample_count':args.cycles},
        'traffic':{'schedule_artifact':'input','offered_count':args.cycles,'accepted_count':args.cycles,'completed_count':args.cycles,'rejected_count':0,'dropped_count':0,'duplicate_output_count':0,'wrong_output_count':0,'unresolved_count':0},
        'metrics':[{'id':'simulation.matched_transitions','value':args.cycles,'unit':'count','statistic':'total','population':'simulator stimulus cycles, not market messages or orders','direction':'context'}],
        'artifacts':artifacts,'limitations':['Finite functional RTL simulation; no physical FPGA, line-rate I/O, formal proof or latency measurement.','Traffic counts describe simulator stimulus cycles, not accepted trading events.','Host reconciliation and frame integrity are trusted external adapter inputs.','Testbench clock period is stimulus, not a device performance claim.']}
    dump('run.json',record)
    print(json.dumps({'record':str(output/'run.json'),'matching_transitions':args.cycles,'physical_latency_ns':None},indent=2))


if __name__=='__main__':main()
