#!/usr/bin/env python
# coding: utf-8

# gitshelve.py, version 0.1
#
# by John Wiegley <johnw@newartisans.com>
#
# This file implements a Python shelve object that uses a branch within the
# current Git repository to store its data, plus a history of all changes to
# that data.  The usage is identical to shelve, with the exception that a
# repository directory or branch name must be specified, and that
# writeback=True is assumed.
#
# Example:
#
#   import gitshelve
#
#   data = gitshelve.open(branch = 'mydata', repository = '/tmp/foo')
#   data = gitshelve.open(branch = 'mydata')  # use current repo
#
#   data['foo/bar/git.c'] = "This is some sample data."
#
#   data.commit("Changes")
#   data.sync()                  # same as data.commit()
#
#   print data['foo/bar/git.c']
#
#   data.close()
#
# If you checkout the 'mydata' branch now, you'll see the file 'git.c' in the
# directory 'foo/bar'.  Running 'git log' will show the change you made.

import re
import os

try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO

from subprocess import Popen, PIPE
from string import split, join

######################################################################

verbose = False

######################################################################

# Utility function for calling out to Git (this script does not try to
# be a Git library, just an interface to the underlying commands).  It
# supports a 'restart' keyword, which will cause a Python function to
# be called on failure.  If that function returns True, the same
# command will be attempted again.  This can avoid costly checks to
# make sure a branch exists, for example, by simply failing on the
# first attempt to use it and then allowing the restart function to
# create it.

class GitError(Exception):
    def __init__(self, cmd, args, kwargs, stderr = None):
        self.cmd = cmd
        self.args = args
        self.kwargs = kwargs
        self.stderr = stderr
        Exception.__init__(self)

    def __str__(self):
        if self.stderr:
            return "Git command failed: git-%s %s: %s" % \
                (self.cmd, self.args, self.stderr)
        else:
            return "Git command failed: git-%s %s" % (self.cmd, self.args)

def git(cmd, *args, **kwargs):
    restart = True
    while restart:
        stdin_mode = None
        if kwargs.has_key('input'):
            stdin_mode = PIPE

        if verbose:
            print "Command: git-%s %s" % (cmd, join(args, ' '))
            if kwargs.has_key('input'):
                print "Input: <<EOF"
                print kwargs['input'],
                print "EOF"

        environ = None
        if kwargs.has_key('repository'):
            environ = os.environ.copy()
            environ['GIT_DIR'] = kwargs['repository']

            git_dir = environ['GIT_DIR']
            if not os.path.isdir(git_dir):
                proc = Popen('git-init', env = environ,
                             stdout = PIPE, stderr = PIPE)
                if proc.wait() != 0:
                    raise GitError('init', [], {}, proc.stderr.read())

        proc = Popen(('git-' + cmd,) + args, env = environ,
                     stdin  = stdin_mode,
                     stdout = PIPE,
                     stderr = PIPE)

        if kwargs.has_key('input'):
            proc.stdin.write(kwargs['input'])
            proc.stdin.close()

        returncode = proc.wait()
        restart = False
        if returncode != 0:
            if kwargs.has_key('restart'):
                if kwargs['restart'](cmd, args, kwargs):
                    restart = True
            else:
                raise GitError(cmd, args, kwargs, proc.stderr.read())

    if not kwargs.has_key('ignore_output'):
        if kwargs.has_key('keep_newline'):
            return proc.stdout.read()
        else:
            return proc.stdout.read()[:-1]


class gitbook:
    """Abstracts a reference to a data file within a Git repository.  It also
    maintains knowledge of whether the object has been modified or not."""
    def __init__(self, shelf, path, name = None):
        self.shelf = shelf
        self.path  = path
        self.name  = name
        self.data  = None
        self.dirty = False

    def get_data(self):
        if self.data is None:
            assert self.name is not None
            self.data = self.deserialize_data(self.shelf.get_blob(self.name))
        return self.data
        
    def set_data(self, data):
        if data != self.data:
            self.name  = None
            self.data  = data
            self.dirty = True

    def serialize_data(self, data):
        return data

    def deserialize_data(self, data):
        return data

    def change_comment(self):
        return None

    def __getstate__(self):
        odict = self.__dict__.copy() # copy the dict since we change it
        del odict['dirty']           # remove dirty flag
        return odict

    def __setstate__(self, ndict):
        self.__dict__.update(ndict) # update attributes
        self.dirty = False


class gitshelve(dict):
    """This class implements a Python "shelf" using a branch within a Git
    repository.  There is no "writeback" argument, meaning changes are only
    written upon calling close or sync.

    This implementation uses a dictionary of gitbook objects, since we don't
    really want to use Pickling within a Git repository (it's not friendly to
    other Git users, nor does it support merging)."""
    ls_tree_pat = re.compile('(040000 tree|100644 blob) ([0-9a-f]{40})\t(start|(.+))$')

    head    = None
    dirty   = False
    objects = None

    def __init__(self, branch = 'master', repository = None,
                 book_type = gitbook):
        self.branch     = branch
        self.repository = repository
        self.book_type  = book_type
        self.init_data()
        dict.__init__(self)

    def init_data(self):
        self.head    = None
        self.dirty   = False
        self.objects = {}

    def git(self, *args, **kwargs):
        if self.repository:
            kwargs['repository'] = self.repository
        return apply(git, args, kwargs)

    def current_head(self):
        return self.git('rev-parse', self.branch)

    def update_head(self, new_head):
        if self.head:
            self.git('update-ref', 'refs/heads/%s' % self.branch, new_head,
                     self.head)
        else:
            self.git('update-ref', 'refs/heads/%s' % self.branch, new_head)
        self.head = new_head

    def read_repository(self):
        self.init_data()
        try:
            self.head = self.current_head()
        except:
            self.head = None

        if not self.head:
            return

        ls_tree = split(self.git('ls-tree', '-r', '-t', '-z', self.head),
                        '\0')
        for line in ls_tree:
            match = self.ls_tree_pat.match(line)
            assert match

            treep = match.group(1) == "040000 tree"
            name  = match.group(2)
            path  = match.group(3)

            parts = split(path, os.sep)
            d     = self.objects
            for part in parts:
                if not d.has_key(part):
                    d[part] = {}
                d = d[part]

            if treep:
                d['__root__'] = name
            else:
                d['__book__'] = self.book_type(self, path, name)

    def open(cls, branch = 'master', repository = None,
             book_type = gitbook):
        shelf = gitshelve(branch, repository, book_type)
        shelf.read_repository()
        return shelf

    open = classmethod(open)

    def get_blob(self, name):
        return self.git('cat-file', 'blob', name, keep_newline = True)

    def hash_blob(self, data):
        return self.git('hash-object', '--stdin', input = data)

    def make_blob(self, data):
        return self.git('hash-object', '-w', '--stdin', input = data)

    def make_tree(self, objects, comment_accumulator = None):
        buf = StringIO()

        root = None
        if objects.has_key('__root__'):
            root = objects['__root__']

        for path in objects.keys():
            if path == '__root__': continue

            obj = objects[path]
            assert isinstance(obj, dict)

            if len(obj.keys()) == 1 and obj.has_key('__book__'):
                book = obj['__book__']
                if book.dirty:
                    if comment_accumulator:
                        comment = book.change_comment()
                        if comment:
                            comment_accumulator.write(comment)

                    book.name  = self.make_blob(book.serialize_data(book.data))
                    book.dirty = False
                    root = None

                buf.write("100644 blob %s\t%s\0" % (book.name, path))

            else:
                tree_root = None
                if obj.has_key('__root__'):
                    tree_root = obj['__root__']

                tree_name = self.make_tree(obj, comment_accumulator)
                if tree_name != tree_root:
                    root = None

                buf.write("040000 tree %s\t%s\0" % (tree_name, path))

        if root is None:
            name = self.git('mktree', '-z', input = buf.getvalue())
            objects['__root__'] = name
            return name
        else:
            return root

    def make_commit(self, tree_name, comment):
        if not comment: comment = ""
        if self.head:
            name = self.git('commit-tree', tree_name, '-p', self.head,
                       input = comment)
        else:
            name = self.git('commit-tree', tree_name, input = comment)

        self.update_head(name)
        return name

    def commit(self, comment = None):
        if not self.dirty:
            return self.head

        accumulator = None
        if comment is None:
            accumulator = StringIO()
        
        # Walk the objects now, creating and nesting trees until we end up
        # with a top-level tree.  We then create a commit out of this tree.
        tree = self.make_tree(self.objects, accumulator)
        if accumulator:
            comment = accumulator.getvalue()
        name = self.make_commit(tree, comment)

        self.dirty = False
        return name

    def sync(self):
        self.commit()

    def close(self):
        if self.dirty:
            self.sync()
        del self.objects        # free it up right away

    def dump_objects(self, fd, indent = 0, objects = None):
        if objects is None:
            objects = self.objects

        if objects.has_key('__root__') and indent == 0:
            fd.write('%stree %s\n' % (" " * indent, objects['__root__']))
            indent += 2

        keys = objects.keys()
        keys.sort()
        for key in keys:
            if key == '__root__': continue
            assert isinstance(objects[key], dict)

            if objects[key].has_key('__book__'):
                book = objects[key]['__book__']
                if book.name:
                    kind = 'blob ' + book.name
                else:
                    kind = 'blob'
            else:
                if objects[key].has_key('__root__'):
                    kind = 'tree ' + objects[key]['__root__']
                else:
                    kind = 'tree'

            fd.write('%s%s: %s\n' % (" " * indent, kind, key))

            if kind[:4] == 'tree':
                self.dump_objects(fd, indent + 2, objects[key])

    def get_tree(self, path, make_dirs = False):
        parts = split(path, os.sep)
        d     = self.objects
        for part in parts:
            if make_dirs and not d.has_key(part):
                d[part] = {}
            d = d[part]
        return d

    def __getitem__(self, path):
        try:
            d = self.get_tree(path)
        except KeyError:
            raise KeyError(path)

        if len(d.keys()) == 1:
            return d['__book__'].get_data()
        raise KeyError(path)

    def __setitem__(self, path, data):
        try:
            d = self.get_tree(path, make_dirs = True)
        except KeyError:
            raise KeyError(path)
        if len(d.keys()) == 0:
            d['__book__'] = self.book_type(self, path)
        d['__book__'].set_data(data)
        self.dirty = True

    def prune_tree(self, objects, paths):
        if len(paths) > 1:
            self.prune_tree(objects[paths[0]], paths[1:])
        del objects[paths[0]]

    def __delitem__(self, path):
        try:
            self.prune_tree(self.objects, split(path, os.sep))
        except KeyError:
            raise KeyError(path)

    def __contains__(self, path):
        d = self.get_tree(path)
        return len(d.keys()) == 1 and d.has_key('__book__')

    def walker(self, kind, objects, path = ''):
        for item in objects.items():
            if item[0] == '__root__': continue
            assert isinstance(item[1], dict)

            if path:
                key = join((path, item[0]), os.sep)
            else:
                key = item[0]

            if len(item[1].keys()) == 1 and item[1].has_key('__book__'):
                value = item[1]['__book__']
                if kind == 'keys':
                    yield key
                elif kind == 'values':
                    yield value
                else:
                    assert kind == 'items'
                    yield (key, value)
            else:
                for obj in self.walker(kind, item[1], key):
                    yield obj

        raise StopIteration

    def __iter__(self):
        return self.iterkeys()
    
    def iteritems(self):
        return self.walker('items', self.objects)

    def keys(self):
        k = []
        for key in self.iterkeys():
            k.append(key)
        return k

    def iterkeys(self):
        return self.walker('keys', self.objects)

    def itervalues(self):
        return self.walker('values', self.objects)

    def __getstate__(self):
        self.sync()                  # synchronize before persisting
        odict = self.__dict__.copy() # copy the dict since we change it
        del odict['dirty']           # remove dirty flag
        return odict

    def __setstate__(self, ndict):
        self.__dict__.update(ndict) # update attributes
        self.dirty = False

        # If the HEAD reference is out of date, throw away all data and
        # rebuild it.
        if not self.head or self.head != self.current_head():
            self.read_repository()


def open(branch = 'master', repository = None, book_type = gitbook):
    return gitshelve.open(branch, repository, book_type)

# gitshelve.py ends here
