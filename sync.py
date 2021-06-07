import hashlib
import os
import shutil
from pathlib import Path


def sync(source, dest):
    # imperative shell step 1, gather inputs, 命令式的
    source_hashes = read_paths_and_hashes(source)
    dest_hashes = read_paths_and_hashes(dest)

    # step 2: call functional core, 这是核心逻辑
    actions = determine_actions(source_hashes, dest_hashes, source, dest)

    # imperative shell step 3, apply outputs, 命令式的
    for action, *paths in actions:
        if action == "COPY":
            shutil.copyfile(*paths)
        if action == "MOVE":
            shutil.move(*paths)
        if action == "DELETE":
            os.remove(paths[0])


# 所有的外部依赖都通过参数注入
def synchronise_dirs(reader, filesystem, filesystem2, source_root, dest_root):
    source_hashes = reader(source_root)
    dest_hashes = reader(dest_root)

    actions = determine_actions(source_hashes, dest_hashes, source_root, dest_root)
    for action, *paths in actions:
        if action == "COPY":
            filesystem.copyfile(*paths)
        if action == "MOVE":
            filesystem.move(*paths)
        if action == "DELETE":
            filesystem2.remove(paths[0])


BLOCKSIZE = 65536


def hash_file(path):
    hasher = hashlib.sha1()
    with path.open("rb") as file:
        buf = file.read(BLOCKSIZE)
        while buf:
            hasher.update(buf)
            buf = file.read(BLOCKSIZE)
    return hasher.hexdigest()


def read_paths_and_hashes(root):
    hashes = {}
    for folder, _, files in os.walk(root):
        for fn in files:
            hashes[hash_file(Path(folder) / fn)] = fn
    return hashes


def determine_actions(source_hashes, dest_hashes, source_folder, dest_folder):
    for sha, filename in source_hashes.items():
        if sha not in dest_hashes:
            sourcepath = Path(source_folder) / filename
            destpath = Path(dest_folder) / filename
            yield "COPY", sourcepath, destpath

        elif dest_hashes[sha] != filename:
            olddestpath = Path(dest_folder) / dest_hashes[sha]
            newdestpath = Path(dest_folder) / filename
            yield "MOVE", olddestpath, newdestpath

    for sha, filename in dest_hashes.items():
        if sha not in source_hashes:
            yield "DELETE", Path(dest_folder) / Path(filename)
