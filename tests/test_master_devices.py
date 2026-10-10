"""Device commands on the master track, and track deletion. No Ableton needed."""

import pytest

from tests.test_remote_script_bridge import _load_script_module, make_instance


class FakeParam(object):
    def __init__(self, name, value):
        self.name = name
        self.value = value
        self.min = -24.0
        self.max = 0.0


class FakeDevice(object):
    name = "Limiter"
    class_name = "Limiter"
    can_have_chains = False
    can_have_drum_pads = False

    def __init__(self):
        self.parameters = [FakeParam("Device On", 1.0), FakeParam("Ceiling", 0.0)]


class FakeTrack(object):
    def __init__(self, name, devices=()):
        self.name = name
        self.devices = list(devices)


class FakeSong(object):
    def __init__(self):
        self.tracks = [FakeTrack("Drums"), FakeTrack("4-Audio")]
        self.return_tracks = []
        self.master_track = FakeTrack("Master", [FakeDevice()])

    def delete_track(self, index):
        del self.tracks[index]


@pytest.fixture
def inst():
    instance = make_instance(_load_script_module())
    instance._song = FakeSong()
    return instance


def test_set_master_device_parameter(inst):
    result = inst._set_device_parameter(0, 0, 1, -1.0, "master")
    assert result["name"] == "Ceiling"
    assert inst._song.master_track.devices[0].parameters[1].value == -1.0


def test_master_device_out_of_range(inst):
    with pytest.raises(IndexError, match="Device index out of range"):
        inst._set_device_parameter(0, 3, 1, -1.0, "master")


def test_delete_track(inst):
    assert inst._delete_track(1) == {"deleted": 1, "name": "4-Audio", "track_count": 1}
