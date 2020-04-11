try:
    from sys import _getframe
    getframe = _getframe
except ImportError:
    getframe = None

from traceback import walk_stack


def is_setuptime() -> bool:
    'Return `True` if called from setup.'
    if getframe is None:
        # This is not CPython, can't know if this is setup time
        return False
    for frame, lineno in walk_stack(f=getframe()):
        # @See setup.py
        if frame.f_locals and \
                frame.f_locals.get('_IS_VALIDATEEMAIL_SETUP') is True:
            return True
    return False
