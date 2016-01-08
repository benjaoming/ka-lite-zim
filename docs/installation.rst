============
Installation
============

#. Clone from the Git repository::
    
    git clone https://github.com/benjaoming/ka-lite-zim.git

#. Make sure that while you're installing you are using the same Python environment (virtualenv?) that you also run KA Lite in.

#. Go to the directory and run the installer::

    cd ka-lite-zim/
    pip install -e .  # Installs an editable.

#. Make sure you have KA Lite installed and that you have issued ``kalite start`` at least once. Then edit your ``~/.kalite/settings.py` to contain this::
  
    from kalite.project.settings.base import *
    
    INSTALLED_APPS += [
        'kalite_zim',
        'compressor',
    ]
