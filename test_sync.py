import tempfile
import os
from pathlib import Path
import shutil
from sync import sync, determine_actions, synchronise_dirs, read_paths_and_hashes


class FakeFileSystem(list):

    def copyfile(self, src, dest):
        self.append(('COPY', str(src), str(dest)))

    def move(self, src, dest):
        self.append(('MOVE', str(src), str(dest)))

    def remove(self, dest):
        self.append(('DELETE', str(dest)))


class TestDiE2E:
    """Test 依赖反转的End to End"""

    @staticmethod
    def test_fake_di_sync_copy():
        source = {"sha1": "my-file"}
        dest = {}
        filesystem = FakeFileSystem()
        reader = {"/source": source, "/dest": dest}
        synchronise_dirs(reader.pop, filesystem, filesystem, "/source", "/dest")
        assert filesystem == [("COPY", "/source/my-file", "/dest/my-file")]

    @staticmethod
    def test_fake_di_sync_delete():
        source = {}
        dest = {"sha1": "my-file"}
        filesystem = FakeFileSystem()
        reader = {"/source": source, "/dest": dest}
        synchronise_dirs(reader.pop, filesystem, filesystem, "/source", "/dest")
        assert filesystem == [('DELETE', '/dest/my-file')]

    @staticmethod
    def test_fake_di_sync_move():
        source = {"sha1": "my-file", "sha2": "my-file2"}
        dest = {"sha1": "my-file", "sha2": "my-file3"}
        filesystem = FakeFileSystem()
        reader = {"/source": source, "/dest": dest}
        synchronise_dirs(reader.pop, filesystem, filesystem, "/source", "/dest")
        assert filesystem == [('MOVE', '/dest/my-file3', '/dest/my-file2')]

    @staticmethod
    def test_di_sync_when_a_file_exists_in_the_source_but_not_the_destination():
        try:
            source = tempfile.mkdtemp()
            dest = tempfile.mkdtemp()

            content = "I am a very useful file"
            (Path(source) / "my-file").write_text(content)

            synchronise_dirs(read_paths_and_hashes, shutil, os, source, dest)

            expected_path = Path(dest) / "my-file"
            assert expected_path.exists()
            assert expected_path.read_text() == content

        finally:
            shutil.rmtree(source)
            shutil.rmtree(dest)

    @staticmethod
    def test_di_sync_when_a_file_has_been_renamed_in_the_source():
        try:
            source = tempfile.mkdtemp()
            dest = tempfile.mkdtemp()

            content = "I am a file that was renamed"
            source_path = Path(source) / "source-filename"
            old_dest_path = Path(dest) / "dest-filename"
            expected_dest_path = Path(dest) / "source-filename"
            source_path.write_text(content)
            old_dest_path.write_text(content)

            synchronise_dirs(read_paths_and_hashes, shutil, os, source, dest)

            assert old_dest_path.exists() is False
            assert expected_dest_path.read_text() == content

        finally:
            shutil.rmtree(source)
            shutil.rmtree(dest)


class TestE2E:
    """Test End to End"""

    @staticmethod
    def test_when_a_file_exists_in_the_source_but_not_the_destination():
        try:
            source = tempfile.mkdtemp()
            dest = tempfile.mkdtemp()

            content = "I am a very useful file"
            (Path(source) / "my-file").write_text(content)

            sync(source, dest)

            expected_path = Path(dest) / "my-file"
            assert expected_path.exists()
            assert expected_path.read_text() == content

        finally:
            shutil.rmtree(source)
            shutil.rmtree(dest)

    @staticmethod
    def test_when_a_file_has_been_renamed_in_the_source():
        try:
            source = tempfile.mkdtemp()
            dest = tempfile.mkdtemp()

            content = "I am a file that was renamed"
            source_path = Path(source) / "source-filename"
            old_dest_path = Path(dest) / "dest-filename"
            expected_dest_path = Path(dest) / "source-filename"
            source_path.write_text(content)
            old_dest_path.write_text(content)

            sync(source, dest)

            assert old_dest_path.exists() is False
            assert expected_dest_path.read_text() == content

        finally:
            shutil.rmtree(source)
            shutil.rmtree(dest)


def test_when_a_file_exists_in_the_source_but_not_the_destination():
    source_hashes = {"hash1": "fn1"}
    dest_hashes = {}
    actions = determine_actions(source_hashes, dest_hashes, Path("/src"), Path("/dst"))
    assert list(actions) == [("COPY", Path("/src/fn1"), Path("/dst/fn1"))]


def test_when_a_file_has_been_renamed_in_the_source():
    source_hashes = {"hash1": "fn1"}
    dest_hashes = {"hash1": "fn2"}
    actions = determine_actions(source_hashes, dest_hashes, Path("/src"), Path("/dst"))
    assert list(actions) == [("MOVE", Path("/dst/fn2"), Path("/dst/fn1"))]
