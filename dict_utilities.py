# Dictionary-Utilities
Utilities for a python dictionary

import collections
import contextlib
import copy
import datetime
import inspect
import re
import uuid
import six

PATH_DELIMITERS = [",", ".", "[", "]"]

PII_KEYS = ["dob", "ssn", "driver_license_no", "business_tax_id"]


def _split_and_trim(string, *delimiters):
    pattern = "|".join(map(re.escape, delimiters))
    return list(filter(None, re.split(pattern, string, 0)))


def parse_path(path):
    if isinstance(path, six.string_types):
        path = _split_and_trim(path, *PATH_DELIMITERS)

    for key in path:
        if isinstance(key, six.string_types):
            for k in _split_and_trim(key, *PATH_DELIMITERS):
                yield k
        else:
            yield key


def getpath(obj, path, default=None):
    """Gets the value following the path list, if the path doesn't exitst
    returns the default value
    Args:
        obj(dict): list or dict or object to examine
        path(list|str): list of keys to follow to examine
    Returns:
        value located in the path location

    Example:
        >>> getpath({'one': {'two': {3: 4}}}, ['one', 'two'])
        {3: 4}

        >>> getpath({'one': {'two': {3: 4}}}, 'one.two')
        {3: 4}

        >>> getpath({'one': {'two': {'three': 4}}}, ['one', 'four'])

        >>> getpath({'one': {'two': {'three': 4}}}, 'one.four')

        >>> getpath({'one': ['two', {'three': [4, 5]}]}, ['one', 1, 'three'])
        [4, 5]

        >>> getpath(['one', {'two': {'three': [4, 5]}}], '[1].two.three.[0]')
        4

        >>> getpath({'one': ['two', {'three': [4, 5]}]}, 'one[1].three')
        [4, 5]

        >>> getpath([range(50)], [0, 42])
        42

        >>> getpath([[[[[[[[[[42]]]]]]]]]], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        42
    """
    for key in parse_path(path):
        try:
            try:
                obj = getattr(obj, key)
            except (AttributeError, TypeError):
                try:
                    obj = obj[key]
                except TypeError:
                    obj = obj[int(key)]
        except (KeyError, IndexError, TypeError, AttributeError, ValueError):
            obj = default

        if obj is None:
            break

    return obj


def convert_values_to_string(obj):
    if isinstance(obj, dict):
        return {k: convert_values_to_string(obj[k]) for k in obj}
    elif isinstance(obj, list):
        return [convert_values_to_string(val) for val in obj]
    elif obj is None:
        return None
    else:
        return six.text_type(obj)


def normalize_strings(obj):
    if isinstance(obj, dict):
        return {normalize_strings(k): normalize_strings(obj[k]) for k in sorted(obj)}
    elif isinstance(obj, list):
        return [normalize_strings(val) for val in obj]
    else:
        return six.text_type(obj) if isinstance(obj, six.string_types) else obj


def whitelist_dict(data, white_list, copy_data=True):
    """Whitelist data according to the list of elements passed in. Data keys not in whitelist and present should be redacted.
    Args:
        data (dict): single-layer dictionary that contains sensitive data
        white_list (list): list of keys in data whose values should be shown
        copy_data (bool, optional): Whether to make a deepcopy of the data before whitelisting it
    Returns:
        Returns the data whitelisted.
    """
    white_listed_data = copy.deepcopy(data) if copy_data else data
    for field in white_listed_data:
        if field not in white_list and white_listed_data[field]:
            white_listed_data[field] = "REDACTED"

    return white_listed_data


class Bunch(object):
    """
    A dot-accessible dictionary (a la JavaScript objects)

    # Returns a stand-in class for a class
    # with only the necessary attributes needed for test in question.
    # In other words, the following mock would be used in a function
    """

    def __init__(self, **kwds):
        self.__dict__.update(kwds)

    def __eq__(self, other):
        if isinstance(other, dict):
            return self.__dict__ == other
        else:
            return self.__dict__ == other.__dict__

    def __gt__(self, other):
        log.warning(
            "py3 does not allow comparison with dictionaries {}.__gt__({}, {})".format(
                type(self), six.text_type(self), six.text_type(other)
            )
        )
        return False

    def __lt__(self, other):
        log.warning(
            "py3 does not allow comparison with dictionaries {}.__lt__({}, {})".format(
                type(self), six.text_type(self), six.text_type(other)
            )
        )
        return False

    def __hash__(self):
        """ py3 making the object hashable """
        return hash(tuple(self.__dict__))

    def __repr__(self):
        return repr(self.__dict__)


class LoggedDict(dict):
    """
    This class wraps a dict to figure out how that dict is being used
    """

    def __init__(self, *args, **kwargs):
        super(LoggedDict, self).__init__(*args, **kwargs)
        self.log("__init__", six.text_type(args), six.text_type(kwargs))
        self.update(*args, **kwargs)

    def __getitem__(self, key):
        val = super(LoggedDict, self).__getitem__(key)
        self.log("__getitem__", six.text_type(key), six.text_type(val))
        return val

    def __setitem__(self, key, val):
        self._rpr_("__setitem__", six.text_type(key), six.text_type(val))
        super(LoggedDict, self).__setitem__(key, val)

    def get(self, key, *args):
        val = super(LoggedDict, self).get(key, *args)
        self.log("get", six.text_type(key), six.text_type(val))
        return val

    def set(self, key, val):
        self._rpr_("set", six.text_type(key), six.text_type(val))
        super(LoggedDict, self).set(key, val)

    def log(self, method, key, val):
        # TODO: look into using traceback.format_stack if we run into any
        # problems with depth of stack.
        s = inspect.stack()
        msg = "****{}[{}] = {} -> {}".format(
            six.text_type(method), six.text_type(key), six.text_type(val), six.text_type(s[2][1:3])
        )
        log.debug(msg)


def recursive_primitive(i):
    """
    Validates dictionary recursively.

    Example:
        >>> print(recursive_primitive(u'hello'))
        hello
        >>> print(recursive_primitive(b'world'))
        world
        >>> recursive_primitive(1)
        1
        >>> recursive_primitive(None)
        >>> recursive_primitive(True)
        True
        >>> assert isinstance(recursive_primitive(datetime.date.today()), datetime.date)
        >>> assert isinstance(recursive_primitive(datetime.datetime.utcnow()), datetime.datetime)
        >>> assert isinstance(recursive_primitive(uuid.uuid1()), uuid.UUID)
        >>> recursive_primitive({1: 2})
        {1: 2}
        >>> recursive_primitive([1])
        [1]
        >>> recursive_primitive((1,))
        [1]
        >>> recursive_primitive(type(str('type'), (object,), {})())
        Traceback (most recent call last):
        ...
        TypeError: Unsupported value of type <class 'dt_platform_utils.utils.dict_utils.type'>
    """
    if isinstance(i, six.string_types + six.integer_types + (bool, float, type(None), datetime.date, uuid.UUID)):
        return i
    elif not six.PY2 and isinstance(i, bytes):
        return i.decode("ascii")
    elif isinstance(i, collections.Mapping):
        return {k: recursive_primitive(v) for k, v in i.items()}
    elif isinstance(i, collections.Iterable):
        return [recursive_primitive(j) for j in i]
    else:
        raise TypeError("Unsupported value of type {!r}".format(type(i)))


missing = object()


@contextlib.contextmanager
def push_keys(mapping, **kwargs):
    """
    Temporarily assign keys to a dictionary
    """
    backup = {k: mapping.get(k, missing) for k in kwargs}
    mapping.update(kwargs)
    yield
    mapping.update(backup)
    for k, v in backup.items():
        if v is missing:
            del mapping[k]


def traverse_range_key_dict(member, range_key_dict):
    """
    Returns the value if given member(strictly integer) is found within the range of the dictionary key ranges
    else returns None
    Args:
        member: Integer
        range_key_dict: Dictionary with keys as range (tuple)
    Returns:
        return the key's value or None

    Example:
        # >>> traverse_range_key_dict(1, {(0, 100): 'ABC'})
        # 'ABC'
        # >>> traverse_range_key_dict(0, {(0, 100): 'ABC'})
        # 'ABC'
        # >>> traverse_range_key_dict(123, {(0, 100): 'ABC'})
        # >>> traverse_range_key_dict(100, {(0, 100): 'ABC'})
    """
    for key_range, value in range_key_dict.items():
        if member in six.moves.xrange(*key_range):
            return value


def _recursive_mask_values(obj, *pii_keys):
    """
    Recursively finds keys of the names specified and replaces the
    corresponding values with 'X'.

    Args:
        data(dict): a nested dict/list structure to search for keys under

    Example:
        data = {
            "dtapplication": {
                "applicants": [
                    {
                        "name": "Meow Mix",
                        "ssn": "12312453"
                    },
                    {
                        "name": "Meow Mix",
                        "ssn": "12312453"
                    }
                ]
            }
        }
        print recursive_mask_values(data)
        {
            "dtapplication": {
                "applicants": [
                    {
                        "name": "Meow Mix",
                        "ssn": "X"
                    },
                    {
                        "name": "Meow Mix",
                        "ssn": "X"
                    }
                ]
            }
        }
    """
    if isinstance(obj, dict):
        return {
            key: "X" if key in pii_keys and val else _recursive_mask_values(val, *pii_keys) for key, val in obj.items()
        }
    elif isinstance(obj, list):
        return [_recursive_mask_values(val, *pii_keys) for val in obj]
    elif isinstance(obj, tuple):
        return tuple([_recursive_mask_values(val, *pii_keys) for val in obj])
    else:
        return obj


def safe_mask_values(data, *pii_keys):
    """
    Recursively masks values under the given key names for the purpose of logging.
    Does not alter the original object to prevent ruining it for any other use.
    """
    obj = copy.deepcopy(data)
    return _recursive_mask_values(obj, *pii_keys)


def _recursively_alter_values_in_dict(obj, fn, *keys):
    """
    Recursively finds keys of the names specified and massages the
    corresponding values with the function that is passed as the parameter.

    Args:
        data(dict): a nested dict structure


    Example:
        data = {
            "dtapplication": {
                "applicants": [
                    {
                        "name": "Test Emp",
                        "link_url": "app/test"
                    },
                    {
                        "name": "Tester Emp",
                        "link_url": "app/tester"
                    }
                ]
            }
        }
        print _recursively_alter_values_in_dict(data, func, "link_url")
        {
            "dtapplication": {
                "applicants": [
                    {
                        "name": "Test Emp",
                        "link_url": func(link_url) --> The value would be the return value of the function "func"
                    },
                    {
                        "name": "Tester Emp",
                        "link_url": func(link_url)
                    }
                ]
            }
        }
    """

    if isinstance(obj, dict):
        return {
            key: fn(val) if key in keys and val else _recursively_alter_values_in_dict(val, fn, *keys)
            for key, val in obj.items()
        }

    return obj


def check_dict_empty(input_dict):
    """
    Method to check if the dictionary given is empty
    Returns True if atleast one of the values in the dictionary is non-empty
    """
    return {True for k, v in input_dict.items() if v}


def find_key_in_dict(node, key):
    """
    To find keys that are within dictionaries that are nested within list of lists etc
    :param node: Nested dictionary
    :param key: Key
    :return: list that contains the key
    """
    if isinstance(node, list):
        # To find the key in the list in the intermediate step
        for item in node:
            for key in find_key_in_dict(item, key):
                yield key
    elif isinstance(node, dict):
        # To find the key in the dict in the intermediate step
        if key in node:
            yield key
        for items in node.values():
            for key in find_key_in_dict(items, key):
                yield key


def key_in_dict(node, key):
    """
    True if key is in the nested dictionary
    """
    return True if key in find_key_in_dict(node, key) else False
