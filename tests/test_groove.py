"""Remote Script groove pool commands against fake Live objects. No Ableton needed."""

import pytest

from tests.test_remote_script_bridge import _load_script_module, make_instance


class FakeGroove(object):
    def __init__(self, name):
        self.name = name
        self.timing_amount = 100.0
        self.random_amount = 0.0
        self.velocity_amount = 0.0
        self.quantization_amount = 0.0


class FakeClip(object):
    name = "Beat"
    groove = None


class FakeSlot(object):
    def __init__(self, clip):
        self.clip = clip
        self.has_clip = clip is not None


class FakeTrack(object):
    def __init__(self):
        self.clip_slots = [FakeSlot(FakeClip()), FakeSlot(None)]


class FakeGroovePool(object):
    def __init__(self):
        self.grooves = [FakeGroove("MPC 16 Swing-58")]


class FakeSong(object):
    def __init__(self):
        self.tracks = [FakeTrack()]
        self.return_tracks = []
        self.groove_pool = FakeGroovePool()
        self.groove_amount = 1.0


@pytest.fixture
def inst():
    instance = make_instance(_load_script_module())
    instance._song = FakeSong()
    return instance


def test_pool_lists_grooves(inst):
    pool = inst._get_groove_pool()
    assert pool["global_amount"] == 1.0
    assert pool["grooves"][0]["name"] == "MPC 16 Swing-58"
    assert pool["grooves"][0]["timing_amount"] == 100.0


def test_apply_clip_groove(inst):
    assert inst._set_clip_groove(0, 0, 0) == {"clip": "Beat", "groove": "MPC 16 Swing-58"}
    assert inst._song.tracks[0].clip_slots[0].clip.groove is inst._song.groove_pool.grooves[0]


def test_set_groove_params(inst):
    result = inst._set_groove_params(0, {"timing_amount": 60, "velocity_amount": 20})
    assert result["timing_amount"] == 60.0
    assert result["velocity_amount"] == 20.0


def test_unknown_amount_is_rejected(inst):
    with pytest.raises(Exception, match="Unknown groove amount 'base'"):
        inst._set_groove_params(0, {"base": 1})


def test_groove_index_out_of_range(inst):
    with pytest.raises(IndexError, match="pool has 1 grooves"):
        inst._set_clip_groove(0, 0, 3)
