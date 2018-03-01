
Installation
------------

This version of the NEX PSP requires Python 3.6 or later


Manually
^^^^^^^^

Clone the repository and navigate into the project directory. 
Make a Python 3 virtual environment and activate it via

::

    python3 -m venv venv
    source venv/bin/activate

or to explicitly install Python 3.6,

::

    virtualenv -p /usr/local/bin/python3.6 venv
    source venv/bin/activate

Then install the requirements via

::

    pip install -r requirements.txt

neo-python
^^^^^^^^^^

You will also need to install ``neo-python`` in a neighboring directory.  Once that is complete, do the following

::

    sudo pip install -e ../neo-python


Start server
============
you can now start the server with the following command:

::

    python manage.py runserver --noreload 8000


you should now be able to visit ``http://127.0.0.1:8000`` in your browser

