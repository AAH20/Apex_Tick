import argparse
import json
from .oracle import Oracle, stimulus
from .protocol import Quote, encode, decode


def main(argv=None):
    parser=argparse.ArgumentParser(prog="apex-tick")
    parser.add_argument("command",choices=["demo"])
    parser.parse_args(argv)
    model=Oracle()
    model.step(stimulus(recover=1))
    payload=encode(Quote(1,0,99,1,1))
    quote=decode(payload,ethernet_frame_valid=True)
    result=model.step(stimulus(valid=1,seq=quote.sequence,instrument=quote.instrument,price=quote.price,qty=quote.quantity,epoch=quote.epoch))
    print(json.dumps({'environment':'python_reference_simulation','payload_hex':payload.hex(),'transition':result,'physical_latency_ns':None,'limitations':['No NIC, Ethernet MAC, exchange connection or FPGA board is exercised.']},indent=2))
    return 0
