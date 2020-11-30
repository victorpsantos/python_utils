import os
import re
import stat


class Path(object):
    def __init__(self, path):
        self.path = os.path.normcase(path)

    def __repr__(self):
        return self.path

    def __bytes__(self):
        """Return the bytes representation of the path.  This is only
        recommended to use under Unix."""
        return os.fsencode(self)

    @property
    def name(self):
        """The final path component, if any."""
        name = self.path.split(os.sep)[-1]
        return name

    @property
    def suffix(self):
        """
        The final component's last suffix, if any.
        This includes the leading period. For example: '.txt'
        """
        # name = self.name
        # i = len(name.split(".")) - 1
        # if 0 < i < len(name) - 1:
        #     return '.' + '.'.join(name.split(".")[-i:])
        # else:
        #     return None
        name = self.name
        i = name.rfind(".")
        if 0 < i < len(name) - 1:
            return name[i:]
        else:
            return ""

    @property
    def suffixes(self):
        """
        A list of the final component's suffixes, if any.
        These include the leading periods. For example: ['.tar', '.gz']
        """
        name = self.name
        if name.endswith("."):
            return []
        name = name.lstrip(".")
        return ["." + suffix for suffix in name.split(".")[1:]]

    @property
    def stem(self):
        """The final path component, minus its last suffix."""
        name = self.name
        i = name.rfind(".")
        if 0 < i < len(name) - 1:
            return name[:i]
        else:
            return name

    @property
    def stat(self):
        """
        Return the result of the stat() system call on this path, like
        os.stat() does.
        """
        return os.stat(self.path)

    @classmethod
    def cwd(cls):
        return cls(os.getcwd())

    @classmethod
    def home(cls):
        return cls(os.path.expanduser("~"))

    def samefile(self, other_path):
        """Return whether other_path is the same or not as this file
        (as returned by os.path.samefile()).
        """
        st = self.stat()
        try:
            other_st = other_path.stat()
        except AttributeError:
            raise AttributeError
        return os.path.samestat(st, other_st)

    def join(self, *args):
        self.path = os.path.join(self.path, *args)
        return self.path

    def scan(self):
        if self.is_dir():
            for entry in os.scandir(self.path):
                yield Path(entry)
        else:
            raise TypeError("Files can't use scan().")

    def walk(self):
        """
        For each directory in the directory tree rooted at top (including top
        itself, but excluding '.' and '..'), yields a tuple with dirpath and
        filenames.
        Dirpath is a string, the path to the directory.
        Filenames is a list of the names of the non-directory files in dirpath.
        """
        files = []
        for entry in os.scandir(self.path):
            if entry.is_dir():
                new_path = Path(entry.path)
                yield from new_path.walk()
            elif entry.is_file():
                files.append(Path(entry.path))
            
        yield self.path, files

    def limited_walk(self, limit, only_in_limit=False):
        """
        """
        if only_in_limit:
            for dirs, files in self.walk():
                if dirs[len(self.path):].count(os.sep) == limit:
                    yield dirs, files
        else:
            for dirs, files in self.walk():
                if dirs[len(self.path):].count(os.sep) <= limit:
                    yield dirs, files

    def glob(self, pattern):
        """
        Iterate over this subtree and yield all existing files (of any
        kind, including directories) matching the given relative pattern.
        """
        if not pattern:
            raise ValueError("Unacceptable pattern: {!r}".format(pattern))
        for entry in os.scandir(self.path):
            if entry.is_file():
                if re.match(rf"(?i).*?.{pattern}$", entry.name):
                    yield Path(entry)

    def rglob(self, pattern):
        """
        Recursively yield all existing files (of any kind, including
        directories) matching the given relative pattern, anywhere in
        this subtree.
        """
        if not pattern:
            raise ValueError("Unacceptable pattern: {!r}".format(pattern))
        for entry in os.scandir(self.path):
            if entry.is_dir():
                new_path = Path(entry)
                yield from new_path.rglob(pattern)
            elif entry.is_file():
                if re.match(rf"(?i).*?.{pattern}$", entry.name):
                    yield Path(entry)

    def is_dir(self):
        """
        Whether this path is a directory.
        """
        try:
            return stat.S_ISDIR(os.stat(self.path).st_mode)
        except OSError:
            return False
        except ValueError:
            # Non-encodable path
            return False

    def is_file(self):
        """
        Whether this path is a directory.
        """
        try:
            return stat.S_ISREG(os.stat(self.path).st_mode)
        except OSError:
            return False
        except ValueError:
            # Non-encodable path
            return False

    def exists(self):
        """
        Whether this path exists.
        """
        try:
            self.stat()
        except OSError as err:
            raise err
            return False
        except ValueError:
            # Non-encodable path
            return False
        return True
