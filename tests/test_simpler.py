"""Simpler slicing control and Live 11 value readout, on fake Live objects."""

import pytest

from tests.test_remote_script_bridge import _load_script_module, make_instance


class FakeSample(object):
    file_path = "C:\\Samples\\Break 100bpm.aif"
    sample_rate = 44100
    length = 441000
    slicing_style = 0
    slicing_beat_division = 2
    slicing_sensitivity = 0.5
    slices = [0, 22050, 44100]


class FakeSimpler(object):
    name = "Break 100bpm"
    playback_mode = 0
    slicing_playback_mode = 0

    def __init__(self):
        self.sample = FakeSample()


class FakeParam(object):
    name = "Ratio"
    value = 0.5
    min = 0.0
    max = 1.0

    def str_for_value(self, value):
        return "4.00 : 1"


class FakeDevice(object):
    name = "Compressor"
    class_name = "Compressor2"
    can_have_chains = False
    can_have_drum_pads = False
    parameters = [FakeParam()]


class FakeTrack(object):
    devices = [FakeSimpler(), FakeDevice()]


class FakeSong(object):
    tracks = [FakeTrack()]
    return_tracks = []


@pytest.fixture
def inst():
    instance = make_instance(_load_script_module())
    instance._song = FakeSong()
    return instance


def test_slice_by_beat(inst):
    info = inst._set_simpler(0, 0, {"playback_mode": 2, "slicing_style": 1, "slicing_beat_division": 0})
    assert info["playback_mode"] == 2
    assert info["slicing_style"] == 1 and info["slicing_beat_division"] == 0
    assert info["slices"] == [0, 22050, 44100]
    assert info["sample"]["sample_rate"] == 44100


def test_unknown_setting_is_rejected(inst):
    with pytest.raises(Exception, match="Unknown Simpler setting 'pitch'"):
        inst._set_simpler(0, 0, {"pitch": 3})


def test_non_simpler_is_rejected(inst):
    with pytest.raises(Exception, match="'Compressor' is not a Simpler"):
        inst._get_simpler(0, 1)


def test_parameters_report_live_11_readout(inst):
    inst._automated_params_for_device = lambda device: []
    params = inst._serialize_device(FakeDevice(), 1)["parameters"]
    assert params[0]["value_string"] == "4.00 : 1"
