import sys
version_info = sys.version_info
if version_info[:2] > (3, 11):
    print(f'WARNING: Newer python version detected! The plugin has only been tested with Python 3.11.')

def install_dependency(dependency_name):
    import subprocess
    import os
    from pathlib import Path

    print(f'{dependency_name} package not found, installing...')
    py_exec = str(sys.executable)
    # Ensure pip is installed
    subprocess.call([py_exec, '-m', 'ensurepip', '--user'])
    # Install packages
    proc = subprocess.Popen([py_exec, '-m', 'pip', 'install', '--user', dependency_name], stderr=subprocess.PIPE)
    _, error = proc.communicate()
    if len(error) > 0:
        print(f'{dependency_name} package installation error! Please try to install the package manually, or run Blender/python as an elevated user!')
    else:
        print(f'{dependency_name} package installed!')

were_packages_installed = False

try:
    import h5py
except ImportError:
    install_dependency('h5py')
    were_packages_installed = True

try:
    import numpy
except ImportError:
    install_dependency('numpy')
    were_packages_installed = True

try:
    import mathutils
except ImportError:
    install_dependency('mathutils')
    were_packages_installed = True

if were_packages_installed:
    print()
    print(f'----------------------------------------------------------------------------')
    print(f'New packages were installed, to activate the plugin, please restart Blender!')
    print(f'----------------------------------------------------------------------------')
    print()
