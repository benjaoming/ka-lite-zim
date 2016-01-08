============
Installation
============

#. Clone from the Git repository::

    git clone https://github.com/benjaoming/ka-lite-zim.git

#. Make sure that while you're installing you are using the same Python
   environment (virtualenv?) that you also run KA Lite in.

#. To install a fresh KA Lite together with ka-lite-zim, you should use virtualenv

   .. code-block:: bash

        pip install virtualenv      # Installs virtualenv
                                    # ...prepend "sudo" for system-wide
        cd ka-lite-zim/             # Go to the source folder
        virtualenv ./venv           # Creates a new virtualenv in ./venv
        source ./venv/bin/activate  # Activates the virtualenv
        pip install -e .            # Installs an editable
    
   If you already have KA Lite installed on your system, just CD to the
   directory and run the installer, provided that you have already activated
   the environment that KA Lite runs in:
    
   .. code-block:: bash

        cd ka-lite-zim/
        python setup.py install  # Add sudo in front if KA Lite is installed system-wide

#. Make sure you have KA Lite installed and that you have issued ``kalite start`` at least once. Then edit your ``~/.kalite/settings.py` to contain this::
  
    from kalite.project.settings.base import *
    
    INSTALLED_APPS += [
        'kalite_zim',
        'compressor',
    ]


.. note ::
    If you install as an editable with ``pip install -e .``, then issuing
    ``git pull && pip install -e .`` from the source directory is enough to
    update the software. But remember the latter as dependencies might have changed.

.. warning ::
    If you install as an editable with, you cannot delete the source directory
    after installing!!

.. warning ::
    We require a specific version of KA Lite for ka-lite-zim. Therefore, if you
    already have KA Lite on the system, we recommend a virtualenv.
