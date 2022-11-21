#!/usr/bin/env python3

import argparse
import binascii
import os
import sys
import zlib


class GitObject(object):
    """Class that wraps around a Git object."""

    def __init__(self, git_root, object_hash):
        self.git_root = git_root
        self.object_hash = object_hash
        self._raw_data = None
        self._data = None
        self._type = None
        self._size = None
        self._contents = None
        if not os.path.isdir(self.git_root):
            raise ValueError(
                "Directory {0} does not exist!".format(
                    self.git_root))
        object_dir = self.object_hash[:2]
        object_filename = self.object_hash[2:]
        self.filename = os.path.join(self.git_root,
                                     ".git",
                                     "objects",
                                     object_dir,
                                     object_filename)
        if not os.path.isfile(self.filename):
            raise ValueError(
                "Unable to find git object: {0}".format(
                    self.object_hash))
        with open(self.filename, "rb") as file_obj:
            self._raw_data = file_obj.read()
        self._data = zlib.decompress(self._raw_data)

    @property
    def type(self):
        """Returns a string indicating the type of the object."""
        if self._type is None:
            self._type = self._data.split(b' ', maxsplit=1)[0].decode()
        return self._type


    @property
    def contents(self):
        if self._contents is None:
            contents = self._data.split(b'\x00', maxsplit=1)[1]
            if self.type in ["blob", "commit"]:
                self._contents = contents.decode()
            elif self.type == "tree":
                self._contents = list()
                while contents != b'':
                    filemode, contents = contents.split(b' ', maxsplit=1)
                    filename, contents = contents.split(b'\x00', maxsplit=1)
                    sha1, contents = contents[:20], contents[20:]
                    filemode = filemode.decode()
                    filename = filename.decode()
                    sha1 = binascii.hexlify(sha1).decode()
                    self._contents.append((filemode, filename, sha1))
            else:
                self._contents = contents
        return self._contents


def main():
    for root, dirs, files in os.walk(".git/objects/"):
        for file in files:
            print(os.path.basename(root) + file)
            git_object = GitObject("./", os.path.basename(root) + file)
            print(git_object.contents)


if __name__ == "__main__":
    main()