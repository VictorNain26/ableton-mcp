"""Resampling: Remote Script commands against fake Live objects, and the
server-side path mapping and transcoding. No Ableton needed."""

import os
import shutil
import subprocess
import wave

import pytest

from MCP_Server import audio
from tests.test_remote_script_bridge import _load_script_module, make_instance


class FakeRouting(object):
    def __init__(self, name):
        self.display_name = name


class FakeClip(object):
    name = "Resample 0001"
    is_audio_clip = True
    is_recording = False
    file_path = "C:\\Users\\me\\Music\\Set Project\\Samples\\Recorded\\0001 Audio.wav"
    length = 8.0


class FakeSlot(object):
    def __init__(self, has_clip=False):
        self.has_clip = has_clip
        self.clip = FakeClip() if has_clip else None
        self.fired_with = None

    def fire(self, record_length=None):
        self.fired_with = ("fire", record_length)


class FakeTrack(object):
    def __init__(self, name, audio_input, slots):
        self.name = name
        self.has_audio_input = audio_input
        self.clip_slots = slots
        self.available_input_routing_types = [
            FakeRouting("Ext. In"), FakeRouting("Resampling"), FakeRouting("1-Drums")]
        self.input_routing_type = self.available_input_routing_types[0]
        self.current_monitoring_state = 1
        self.arm = False


class FakeSong(object):
    def __init__(self):
        self.tempo = 90.0
        self.return_tracks = []
        self.scenes = [object(), object()]
        self.tracks = [
            FakeTrack("Drums", False, [FakeSlot(True), FakeSlot(False)]),
            FakeTrack("Resample", True, [FakeSlot(False), FakeSlot(False)]),
        ]


@pytest.fixture
def inst():
    instance = make_instance(_load_script_module())
    instance._song = FakeSong()
    return instance


def test_start_routes_resampling_and_records(inst):
    result = inst._start_resample(1, 1, 8)
    track = inst._song.tracks[1]
    assert track.input_routing_type.display_name == "Resampling"
    assert track.current_monitoring_state == 2
    assert track.arm is True
    assert track.clip_slots[1].fired_with == ("fire", 8.0)
    assert result == {"track": "Resample", "clip_index": 1, "beats": 8.0, "tempo": 90.0}


def test_start_launches_scene_row_on_other_tracks(inst):
    inst._start_resample(1, 1, 4, scene_index=0)
    assert inst._song.tracks[0].clip_slots[0].fired_with == ("fire", None)
    assert inst._song.tracks[1].clip_slots[0].fired_with is None


def test_rejects_midi_track_and_full_slot(inst):
    with pytest.raises(Exception, match="not an audio track"):
        inst._start_resample(0, 1, 4)
    inst._song.tracks[1].clip_slots[0] = FakeSlot(True)
    with pytest.raises(Exception, match="is not empty"):
        inst._start_resample(1, 0, 4)


def test_missing_resampling_input_lists_inputs(inst):
    inst._song.tracks[1].available_input_routing_types = [FakeRouting("Ext. In")]
    with pytest.raises(Exception, match="No Resampling input on 'Resample'. Inputs: Ext. In"):
        inst._start_resample(1, 1, 4)


def test_finish_waits_for_the_clip_then_disarms(inst):
    track = inst._song.tracks[1]
    track.arm = True
    assert inst._finish_resample(1, 1) == {"done": False}
    track.clip_slots[1] = FakeSlot(True)
    result = inst._finish_resample(1, 1)
    assert result["done"] is True
    assert result["file_path"].endswith("0001 Audio.wav")
    assert track.arm is False


@pytest.mark.skipif(not os.path.isdir("/mnt/c"), reason="needs a WSL /mnt/c mount")
def test_local_path_maps_windows_paths_under_wsl():
    assert audio.local_path("C:\\Users\\me\\a b.wav") == "/mnt/c/Users/me/a b.wav"


def test_local_path_leaves_posix_paths_alone():
    assert audio.local_path("/tmp/x.wav") == "/tmp/x.wav"


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="needs ffmpeg")
def test_to_analysis_wav_converts_24_bit(tmp_path):
    src = tmp_path / "rec.wav"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i",
                    "sine=frequency=440:duration=0.5", "-c:a", "pcm_s24le", str(src)],
                   check=True)
    out = audio.to_analysis_wav(str(src))
    try:
        with wave.open(out, "rb") as wav:
            assert wav.getsampwidth() == 2
            assert wav.getnchannels() == 2
        assert audio.analyze(out)["silent"] is False
    finally:
        os.remove(out)


def test_get_clip_file_reports_path(inst):
    inst._song.tracks[1].clip_slots[1] = FakeSlot(True)
    assert inst._get_clip_file(1, 1)["file_path"].endswith("0001 Audio.wav")


def test_get_clip_file_rejects_empty_slot(inst):
    with pytest.raises(Exception, match="No audio clip in slot 0 on 'Resample'"):
        inst._get_clip_file(1, 0)
