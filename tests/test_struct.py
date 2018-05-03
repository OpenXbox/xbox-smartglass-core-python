import construct
from xbox.sg.utils import struct, adapters


def test_xstruct():
    test_struct = struct.XStruct(
        'a' / construct.Int32ub,
        'b' / construct.Int16ub
    )

    obj = test_struct(a=1, b=2)

    assert test_struct.a.subcon == construct.Int32ub
    assert test_struct.b.subcon == construct.Int16ub
    assert 'a' in test_struct
    assert 'b' in test_struct
    assert obj.container == construct.Container(a=1, b=2)
    assert obj.a == 1
    assert obj.b == 2
    assert obj.build() == b'\x00\x00\x00\x01\x00\x02'

    obj.parse(b'\x00\x00\x00\x02\x00\x03')
    assert obj.container == construct.Container(a=2, b=3)

    obj = test_struct.parse(b'\x00\x00\x00\x03\x00\x04')
    assert obj.container == construct.Container(a=3, b=4)


def test_flatten():
    test_sub = struct.XStruct(
        'c' / construct.Int16ub
    )
    test_struct = struct.XStruct(
        'a' / construct.Int32ub,
        'b' / test_sub
    )

    obj = test_struct(a=1, b=test_sub(c=2))
    flat = struct.flatten(obj.container)

    assert flat == construct.Container(a=1, b=construct.Container(c=2))


def test_terminated_field():
    test_struct = struct.XStruct(
        'a' / adapters.TerminatedField(construct.Int32ub)
    )

    assert test_struct(a=1).build() == b'\x00\x00\x00\x01\x00'
    assert test_struct.parse(b'\x00\x00\x00\x01\x00').container.a == 1

    test_struct = struct.XStruct(
        'a' / adapters.TerminatedField(
            construct.Int32ub, length=4, pattern=b'\xff'
        )
    )

    assert test_struct(a=1).build() == b'\x00\x00\x00\x01\xff\xff\xff\xff'
    assert test_struct.parse(b'\x00\x00\x00\x01\xff\xff\xff\xff').container.a == 1


def test_sgstring():
    test_struct = struct.XStruct(
        'a' / adapters.SGString()
    )

    assert test_struct(a='test').build() == b'\x00\x04test\x00'
    assert test_struct.parse(b'\x00\x04test\x00').container.a == 'test'


def test_fieldin():
    test_struct = struct.XStruct(
        'a' / construct.Int32ub,
        'b' / construct.IfThenElse(
            adapters.FieldIn('a', [1, 2, 3]),
            construct.Int32ub, construct.Int16ub
        )
    )

    assert test_struct(a=1, b=2).build() == b'\x00\x00\x00\x01\x00\x00\x00\x02'
    assert test_struct(a=2, b=2).build() == b'\x00\x00\x00\x02\x00\x00\x00\x02'
    assert test_struct(a=3, b=2).build() == b'\x00\x00\x00\x03\x00\x00\x00\x02'
    assert test_struct(a=4, b=2).build() == b'\x00\x00\x00\x04\x00\x02'
