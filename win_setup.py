from distutils.core import setup
import py2exe

# Run 'python win_setup.py py2exe'

opts = {
    "py2exe": {
        "ascii": True,
        "excludes": ["_ssl"],
        "compressed": True,
        "excludes": ['_ssl',  # Exclude _ssl
                   'pyreadline', 'difflib', 'doctest', 'locale',
                   'optparse', 'pickle', 'calendar'],  # Exclude standard library
        'bundle_files': 1,
    }
}

setup(options=opts, windows=['madness.py'], zipfile=None)
