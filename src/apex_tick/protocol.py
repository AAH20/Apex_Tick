"""Public synthetic ask quote, not an exchange protocol. All integers are network-endian."""
import struct
import zlib
from dataclasses import dataclass

BODY=struct.Struct("!4sBBHQHHIII")
FRAME_BYTES=BODY.size+4

@dataclass(frozen=True)
class Quote:
    sequence: int
    instrument: int
    price: int
    quantity: int
    epoch: int


def encode(quote: Quote) -> bytes:
    body=BODY.pack(b"APXT",1,1,0,quote.sequence,quote.instrument,0,quote.price,quote.quantity,quote.epoch)
    return body+struct.pack("!I",zlib.crc32(body))


def decode(payload: bytes, ethernet_frame_valid: bool) -> Quote:
    if not ethernet_frame_valid: raise ValueError("Ethernet integrity not established")
    if len(payload)!=FRAME_BYTES: raise ValueError("invalid payload length")
    body=payload[:-4]
    if zlib.crc32(body)!=struct.unpack("!I",payload[-4:])[0]: raise ValueError("invalid application CRC")
    magic,version,kind,flags,seq,instrument,reserved,price,qty,epoch=BODY.unpack(body)
    if (magic,version,kind,flags,reserved)!=(b"APXT",1,1,0,0): raise ValueError("unsupported payload format")
    return Quote(seq,instrument,price,qty,epoch)
