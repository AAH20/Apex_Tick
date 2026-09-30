import importlib.util
from pathlib import Path
import pytest
from apex_tick.oracle import Oracle, stimulus
from apex_tick.protocol import Quote, encode, decode, FRAME_BYTES
ROOT=Path(__file__).resolve().parents[1]


def active(**configuration):
    core=Oracle();core.step(stimulus(recover=1,**configuration));return core


def test_wire_roundtrip_and_integrity():
    quote=Quote(2**40,7,12345,10,1)
    payload=encode(quote)
    assert len(payload)==FRAME_BYTES==36
    assert decode(payload,True)==quote
    with pytest.raises(ValueError):decode(payload,False)
    with pytest.raises(ValueError):decode(payload[:-1]+bytes([payload[-1]^1]),True)
    with pytest.raises(ValueError):decode(payload+b'x',True)


def test_duplicate_input_cannot_duplicate_order():
    core=active();first=core.step(stimulus(valid=1));second=core.step(stimulus(valid=1))
    assert first['status']==5 and second['status']==2
    assert len(core.pending)==1 and core.exposure==1


def test_output_stall_preserves_identity_and_exposure():
    core=active();first=core.step(stimulus(valid=1));stalled=core.step(stimulus(valid=1,seq=2,out_ready=0))
    assert stalled['ready']==0 and stalled['order']==first['order']
    assert core.expected==2 and core.exposure==1


def test_terminal_cannot_release_unsent_order_or_double_release():
    core=active();core.step(stimulus(valid=1))
    result=core.step(stimulus(terminal_valid=1,terminal_id=1,out_ready=0))
    assert result['status']==9 and core.exposure==1
    result=core.step(stimulus(terminal_valid=1,terminal_id=1))
    assert result['status']==8 and core.exposure==0
    assert core.step(stimulus(terminal_valid=1,terminal_id=1))['status']==9


@pytest.mark.parametrize('fault',[{'frame_ok':0},{'seq':3},{'instrument':8},{'epoch':0},{'price':0},{'qty':0}])
def test_fault_holds_without_committing(fault):
    core=active();result=core.step(stimulus(valid=1,**fault))
    assert result['hold']==1 and core.exposure==0 and not core.pending


def test_recovery_requires_new_epoch_and_no_unresolved_exposure():
    core=active();core.step(stimulus(valid=1));core.step(stimulus(valid=1,seq=3))
    core.step(stimulus(recover=1,epoch=2));assert core.hold
    core.step(stimulus(terminal_valid=1,terminal_id=1))
    core.step(stimulus(recover=1,epoch=1));assert core.hold
    core.step(stimulus(recover=1,epoch=2,seq=2));assert not core.hold


def test_exposure_and_rate_limits():
    core=active(limit=1,rate_limit=1)
    assert core.step(stimulus(valid=1))['status']==5
    assert core.step(stimulus(valid=1,seq=2))['status']==4
    core.step(stimulus(terminal_valid=1,terminal_id=1))
    assert core.step(stimulus(valid=1,seq=3))['status']==4
    for _ in range(64):core.step(stimulus())
    assert core.step(stimulus(valid=1,seq=4))['status']==5


@pytest.mark.parametrize('seed',[17,31,101])
def test_rtl_matches_independent_oracle(seed):
    spec=importlib.util.spec_from_file_location('apex_verifier',ROOT/'verification/verify.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    assert module.verify(seed,800)['matching_transitions']==800
