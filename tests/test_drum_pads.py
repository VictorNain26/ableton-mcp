"""Remote Script drum pad listing against fake Live objects. No Ableton needed."""

import pytest

from tests.test_remote_script_bridge import _load_script_module, make_instance


class FakePad(object):
    def __init__(self, note, name, filled):
        self.note = note
        self.name = name
        self.chains = [object()] if filled else []


class FakeDevice(object):
    def __init__(self, name, drum):
        self.name = name
        self.can_have_drum_pads = drum
        self.drum_pads = [FakePad(36, "Bass Drum", True), FakePad(37, "C#1", False),
                          FakePad(39, "Hand Clap", True)]


class FakeTrack(object):
    devices = [FakeDevice("909 Core Kit", True), FakeDevice("Saturator", False)]


class FakeSong(object):
    tracks = [FakeTrack()]
    return_tracks = []


@pytest.fixture
def inst():
    instance = make_instance(_load_script_module())
    instance._song = FakeSong()
    return instance


def test_lists_only_filled_pads(inst):
    assert inst._get_drum_pads(0, 0) == {"device": "909 Core Kit", "pads": [
        {"note": 36, "name": "Bass Drum"}, {"note": 39, "name": "Hand Clap"}]}


def test_rejects_non_drum_device(inst):
    with pytest.raises(Exception, match="'Saturator' is not a Drum Rack"):
        inst._get_drum_pads(0, 1)
