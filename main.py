import os, stat, errno, requests, json, base64
import utils

try:
    import _find_fuse_parts
except ImportError:
    pass

import fuse

from fuse import Fuse

fuse.fuse_python_api = (0, 2)

class MyStat(fuse.Stat):
    def __init__(self):
        self.st_mode = 0
        self.st_ino = 0
        self.st_dev = 0
        self.st_nlink = 0
        self.st_uid = 0
        self.st_gid = 0
        self.st_size = 0
        self.st_atime = 0
        self.st_mtime = 0
        self.st_ctime = 0

root = {}
root['.'] = {}
root['.']['type'] = 'dir'
root['.']['stat'] = MyStat()
root['.']['stat'].st_mode = stat.S_IFDIR | 0o755
root['.']['stat'].st_nlink = 2
root['..'] = errno.ENOENT

root['usr'] = {}
root['usr']['.'] = {}
root['usr']['.']['type'] = 'dir'
root['usr']['.']['stat'] = {}
root['usr']['.']['stat'] = MyStat()
root['usr']['.']['stat'].st_mode = stat.S_IFDIR | 0o755
root['usr']['.']['stat'].st_nlink = 2
root['usr']['..'] = root

root['home'] = {}
root['home']['.'] = {}
root['home']['.']['type'] = 'dir'
root['home']['.']['stat'] = {}
root['home']['.']['stat'] = MyStat()
root['home']['.']['stat'].st_mode = stat.S_IFDIR | 0o755
root['home']['.']['stat'].st_nlink = 2
root['home']['..'] = root

root['home']['config'] = {}
root['home']['config']['.'] = {}
root['home']['config']['.']['type'] = 'reg'
root['home']['config']['.']['stat'] = MyStat()
root['home']['config']['.']['stat'].st_mode = stat.S_IFREG | 0o777
root['home']['config']['.']['stat'].st_nlink = 1
root['home']['config']['.']['content'] = b'Hello. This is a configuration file!\n'
root['home']['config']['.']['stat'].st_size = len(root['home']['config']['.']['content'])
root['home']['config']['..'] = root['home']

def search_path(path):
    global root
    if path == '/':
        return root
    current = root
    all = path.rstrip('\n').rstrip('/').lstrip('/').split('/')
    for p in all:
        if p in current:
            current = current[p]
        else:
            return None
    return current

class DontpadFS(Fuse):

    def getattr(self, path):
        if path == '/':
            return root['.']['stat']
        f = search_path(path)
        if not f:
            return -errno.ENOENT
        return f['.']['stat']

    def readdir(self, path, offset):
        f = search_path(path)
        if not f:
            return -errno.ENOENT
        for r in f:
            yield fuse.Direntry(r)

    def open(self, path, flags):
        if not search_path(path):
            return -errno.ENOENT

    def read(self, path, size, offset):
        f = search_path(path)
        if not f:
            return -errno.ENOENT
        slen = len(f['.']['content'])
        if offset < slen:
            if offset + size > slen:
                size = slen - offset
            buf = f['.']['content'][offset:offset+size]
        else:
            buf = b''
        return buf

    def write(self, path, buf, offset):
        f = search_path(path)
        if not f:
            return -errno.ENOENT


def main():

    usage = '''
        DontpadFS

    ''' + Fuse.fusage

    server = DontpadFS(version="%prog " + fuse.__version__,
                     usage=usage,
                     dash_s_do='setsingle')

    server.parse(errex=1)
    server.main()

if __name__ == '__main__':
    main()
