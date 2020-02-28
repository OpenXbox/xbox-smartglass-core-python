from construct import Struct, Int16ub

AUX_PACKET_MAGIC = 0xDEAD

aux_header_struct = Struct(
    'magic' / Int16ub,
    'payload_size' / Int16ub
    # payload
    # hash
)
