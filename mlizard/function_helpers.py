#!/usr/bin/python
# coding=utf-8
from __future__ import division, print_function, unicode_literals

import inspect

def get_signature(f):
    args, varargs_name, kw_wildcard_name, defaults = inspect.getargspec(f)
    defaults = defaults or []
    pos_args = args[:len(args)-len(defaults)]
    kwargs = dict(zip(args[-len(defaults):], defaults))
    return {'name' : f.func_name,
            'args' : args,
            'positional' : pos_args,
            'kwargs' : kwargs,
            'varargs_name' : varargs_name,
            'kw_wildcard_name' : kw_wildcard_name}

def assert_no_missing_args(signature, arguments):
    # check if after all some arguments are still missing
    missing_arguments = [v for v in signature['args'] if v not in arguments]
    if missing_arguments :
        raise TypeError("{}() is missing value(s) for {}".format(signature['name'], missing_arguments))

def assert_no_unexpected_kwargs(signature, kwargs):
    # check for erroneous kwargs
    wrong_kwargs = [v for v in kwargs if v not in signature['args']]
    if wrong_kwargs :
        raise TypeError("{}() got unexpected keyword argument(s): {}".format(signature['name'], wrong_kwargs))

def assert_no_duplicate_args(signature, args, kwargs):
    #check for multiple explicit arguments
    positional_arguments = signature['positional'][:len(args)]
    duplicate_arguments = [v for v in positional_arguments if v in kwargs]
    if duplicate_arguments :
        raise TypeError("{}() got multiple values for argument(s) {}".format(signature['name'], duplicate_arguments))

def apply_options(signature, args, kwargs, options):
    """
    For a given function f and the *args and **kwargs it was called with,
    construct a new dictionary of arguments such that:
      - the original explicit call arguments are preserved
      - missing arguments are filled in by name using options (if possible)
      - default arguments are overridden by options
      - sensible errors are thrown if:
        * you pass an unexpected keyword argument
        * you provide multiple values for an argument
        * after all the filling an argument is still missing
    """
    arguments = dict()
    arguments.update(signature['kwargs']) # weakest: default arguments:
    arguments.update((v, options[v]) for v in signature['args'] if v in options) # options
    arguments.update(kwargs) # keyword arguments
    positional_arguments = dict(zip(signature['positional'], args))
    arguments.update(positional_arguments) # strongest: positional arguments
    return arguments