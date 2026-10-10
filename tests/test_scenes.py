"""Remote Script scene commands against fake Live objects. No Ableton needed."""

import pytest

from tests.test_remote_script_bridge import _load_script_module, make_instance


class FakeScene(object):
    def __init__(self, name=""):
        self.name = name
        self.fired = False

    def fire(self):
        self.fired = True


class FakeSong(object):
    def __init__(self, names):
        self.scenes = [FakeScene(n) for n in names]

    def create_scene(self, index):
        scene = FakeScene()
        if index == -1:
            self.scenes.append(scene)
        else:
            self.scenes.insert(index, scene)
        return scene

    def delete_scene(self, index):
        del self.scenes[index]


@pytest.fixture
def inst():
    instance = make_instance(_load_script_module())
    instance._song = FakeSong(["Intro", "Verse"])
    return instance


def test_create_scene_appends_and_names(inst):
    assert inst._create_scene(-1, "Chorus") == {"index": 2, "name": "Chorus", "scene_count": 3}


def test_create_scene_inserts_at_index(inst):
    assert inst._create_scene(1, "Build")["index"] == 1
    assert [s.name for s in inst._song.scenes] == ["Intro", "Build", "Verse"]


def test_rename_fire_and_delete(inst):
    inst._set_scene_name(1, "Verse 1")
    assert inst._fire_scene(1)["name"] == "Verse 1"
    assert inst._song.scenes[1].fired
    assert inst._delete_scene(0) == {"deleted": 0, "name": "Intro", "scene_count": 1}


def test_scene_index_out_of_range(inst):
    with pytest.raises(IndexError, match="Scene index 5 out of range"):
        inst._fire_scene(5)
