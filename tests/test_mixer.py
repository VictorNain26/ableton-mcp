"""Remote Script mixer commands against fake Live objects. No Ableton needed."""

import pytest

from tests.test_remote_script_bridge import _load_script_module, make_instance


class FakeParam(object):
    def __init__(self, value, display):
        self.value = value
        self.min = 0.0 if display is None else -1.0
        self.max = 1.0
        self._display = display

    def str_for_value(self, value):
        if self._display is not None:
            return self._display(value)
        return "%.1f dB" % (value * 10 - 8.5)


class FakeMixer(object):
    def __init__(self):
        self.volume = FakeParam(0.85, None)
        self.panning = FakeParam(0.5, lambda v: "%dR" % round(v * 50))
        self.sends = []


class FakeTrack(object):
    def __init__(self, name):
        self.name = name
        self.mixer_device = FakeMixer()
        self.mute = False
        self.solo = False


class FakeSong(object):
    def __init__(self):
        self.tracks = [FakeTrack("Drums")]
        self.return_tracks = []
        self.master_track = FakeTrack("Master")


@pytest.fixture
def inst():
    instance = make_instance(_load_script_module())
    instance._song = FakeSong()
    return instance


def test_panning_reports_no_db(inst):
    """A pan display like "25R" must not be parsed as 25 dB."""
    mixer = inst._get_mixer(0)
    assert mixer["panning"]["display"] == "25R"
    assert mixer["panning"]["db"] is None
    assert mixer["volume"]["db"] == 0.0


def test_set_panning_reports_no_db(inst):
    result = inst._set_track_panning(0, -0.5)
    assert result["db"] is None


def test_mixer_reports_mute_and_solo(inst):
    inst._song.tracks[0].mute = True
    mixer = inst._get_mixer(0)
    assert mixer["mute"] is True
    assert mixer["solo"] is False
    assert inst._get_mixer(0, "master")["mute"] is None


def test_set_track_mute_and_solo(inst):
    assert inst._set_track_flag(0, "mute", True) == {"name": "Drums", "mute": True}
    assert inst._set_track_flag(0, "solo", True)["solo"] is True
    assert inst._song.tracks[0].mute is True


def test_master_has_no_mute(inst):
    with pytest.raises(Exception, match="master track has no mute"):
        inst._set_track_flag(0, "mute", True, "master")
