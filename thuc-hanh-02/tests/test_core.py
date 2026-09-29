import json

import pytest

from multicast.receiver import create_socket
from rabbitmq.common import build_order, mode_is_durable
from rabbitmq.consumer import decode_order


def test_build_order_has_required_fields():
    order = build_order(7)
    assert order["maDonHang"] == "DH007"
    assert isinstance(order["danhSachSanPham"], list)
    assert isinstance(order["tongTien"], float)
    assert isinstance(order["thoiGianGuiEpoch"], float)


def test_decode_order_round_trip():
    order = build_order(1)
    assert decode_order(json.dumps(order).encode("utf-8")) == order


def test_decode_order_rejects_missing_fields():
    with pytest.raises(ValueError, match="Thieu truong"):
        decode_order(b'{"maDonHang":"DH001"}')


def test_mode_is_durable():
    assert mode_is_durable("persistent") is True
    assert mode_is_durable("transient") is False
    with pytest.raises(ValueError):
        mode_is_durable("unknown")


def test_multicast_socket_can_be_created():
    sock = create_socket("224.1.1.1", 0, "0.0.0.0", 0.01)
    sock.close()

