# psp_template
A Sample PSP dApp

## Setup

- Clone and setup `neo-python`.  Follow instructions on the readme to get it set up properly
- Change directory to the parent directory of `neo-python` and clone this project
- Then do the following:
```
Workspace$ cd psp_template/
psp_template$ python3.5 -m venv venv
psp_template$ source venv/bin/activate
(venv) psp_template$ sudo pip install -r requirements.txt 
... wait for a while
(venv) psp_template thomassaunders$ 
(venv) psp_template thomassaunders$ sudo pip install -e ../neo-python
... wait for a while
(venv) psp_template thomassaunders$ [ready]

```

## Start server

- you can now start the server with the following command:
- `python manage.py runserver --noreload 8000`
- you should now be able to visit `http://127.0.0.1:8000` in your browser

