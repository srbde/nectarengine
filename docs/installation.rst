Installation
============
The minimal working python version is 3.10.

System Prerequisites
--------------------

On platforms where binary wheels for ``coincurve`` and ``cryptography`` are not precompiled, build tools are required to compile the C extensions.

For Debian and Ubuntu:

.. code:: bash

    sudo apt-get install build-essential libssl-dev python3-dev python3-pip libffi-dev libtool autoconf automake pkg-config

For Fedora and RHEL:

.. code:: bash

    sudo dnf install gcc openssl-devel python3-devel libffi-devel libtool autoconf automake pkgconfig

For OSX:

.. code:: bash

    brew install openssl libtool autoconf automake libffi pkg-config
    export CFLAGS="-I$(brew --prefix openssl)/include $CFLAGS"
    export LDFLAGS="-L$(brew --prefix openssl)/lib $LDFLAGS"

Install nectarengine
--------------------

The recommended way to install and manage dependencies is using `uv <https://docs.astral.sh/uv/>`_:

.. code:: bash

    uv add nectarengine

Alternatively, you can use pip:

.. code:: bash

    pip install -U nectarengine

Manual installation
-------------------
    
You can install nectarengine from this repository if you want the latest development version:

.. code:: bash

    git clone https://github.com/srbde/nectarengine.git
    cd nectarengine
    uv sync
    uv sync --dev

Run tests after install:

.. code:: bash

    uv run pytest
