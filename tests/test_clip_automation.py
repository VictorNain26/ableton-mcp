"""Remote Script clip automation against fake Live objects. No Ableton needed."""

import pytest

from tests.test_remote_script_bridge import _load_script_module, make_instance


class FakeParam(object):
    def __init__(self, name, minimum=0.0, maximum=1.0):
        self.name = name
        self.min = minimum
        self.max = maximum
        self.value = minimum

    def str_for_value(self, value):
        return "%.2f" % value


class FakeEnvelope(object):
    def __init__(self):
        self.steps = []

    def insert_step(self, time, length, value):
        self.steps.append((time, length, value))

    def value_at_time(self, time):
        current = None
        for start, _length, value in self.steps:
            if start <= time:
                current = value
        return current


class FakeClip(object):
    length = 4.0

    def __init__(self):
        self.envelopes = {}

    def automation_envelope(self, param):
        return self.envelopes.get(param.name)

    def create_automation_envelope(self, param):
        self.envelopes[param.name] = FakeEnvelope()
        return self.envelopes[param.name]

    def clear_envelope(self, param):
        self.envelopes.pop(param.name, None)


class FakeSlot(object):
    def __init__(self, clip):
        self.clip = clip
        self.has_clip = clip is not None


class FakeMixer(object):
    def __init__(self):
        self.volume = FakeParam("Track Volume")
        self.panning = FakeParam("Track Panning", -1.0, 1.0)
        self.sends = [FakeParam("A-Reverb")]


class FakeDevice(object):
    def __init__(self):
        self.parameters = [FakeParam("Device On"), FakeParam("Frequency")]


class FakeTrack(object):
    def __init__(self):
        self.name = "Pad"
        self.mixer_device = FakeMixer()
        self.devices = [FakeDevice()]
        self.clip_slots = [FakeSlot(FakeClip()), FakeSlot(None)]


class FakeSong(object):
    def __init__(self):
        self.tracks = [FakeTrack()]
        self.return_tracks = []


@pytest.fixture
def inst():
    instance = make_instance(_load_script_module())
    instance._song = FakeSong()
    return instance


def device_target():
    return {"type": "device", "device_index": 0, "parameter_index": 1}


def test_ramp_is_drawn_as_steps(inst):
    result = inst._set_clip_automation(
        0, 0, device_target(),
        [{"time": 0, "value": 0.0}, {"time": 1, "value": 1.0}], resolution=0.25)
    assert result == {"parameter": "Frequency", "points": 2, "steps": 5}
    steps = inst._song.tracks[0].clip_slots[0].clip.envelopes["Frequency"].steps
    assert steps == [(0.0, 0.25, 0.0), (0.25, 0.25, 0.25), (0.5, 0.25, 0.5),
                     (0.75, 0.25, 0.75), (1.0, 0.25, 1.0)]


def test_points_are_sorted_and_clamped(inst):
    inst._set_clip_automation(
        0, 0, {"type": "panning"},
        [{"time": 2, "value": 5.0}, {"time": 0, "value": -5.0}], resolution=2.0)
    steps = inst._song.tracks[0].clip_slots[0].clip.envelopes["Track Panning"].steps
    assert steps == [(0.0, 2.0, -1.0), (2.0, 2.0, 1.0)]


def test_setting_replaces_existing_envelope(inst):
    inst._set_clip_automation(0, 0, {"type": "volume"}, [{"time": 0, "value": 0.2}])
    inst._set_clip_automation(0, 0, {"type": "volume"}, [{"time": 0, "value": 0.7}])
    steps = inst._song.tracks[0].clip_slots[0].clip.envelopes["Track Volume"].steps
    assert [s[2] for s in steps] == [0.7]


def test_read_back_and_clear(inst):
    inst._set_clip_automation(0, 0, {"type": "send", "send_index": 0},
                              [{"time": 0, "value": 0.5}])
    read = inst._get_clip_automation(0, 0, {"type": "send", "send_index": 0}, resolution=2.0)
    assert read["has_envelope"] is True
    assert [s["value"] for s in read["samples"]] == [0.5, 0.5]
    inst._clear_clip_automation(0, 0, {"type": "send", "send_index": 0})
    assert inst._get_clip_automation(0, 0, {"type": "send", "send_index": 0})["has_envelope"] is False


def test_empty_slot_is_rejected(inst):
    with pytest.raises(Exception, match="No clip in slot 1"):
        inst._set_clip_automation(0, 1, device_target(), [{"time": 0, "value": 0.5}])
