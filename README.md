<p align="center">
  <img
    src="http://neonexchange.org/img/NEX-logo.svg"
    width="125px;">
    
</p>
<h3 align="center">NEX Fiat Integrator Template</h3>
<p align="center">A template dApp for NEX Fiat Integrators on the NEO Blockchain</p>
<hr/>

- [Install](#install)
- [Run](#run)
- [NEX Extension](#NexExtension)
- [Settings](#settings)
- [License](#license)

## Install

Setup requires Python 3.6 or later, and all dependencies of `neo-python`.  Please consult [setup instructions](https://github.com/CityOfZion/neo-python) if you are having issues. Optionally requires an installation of `Postgres`

1. Clone and setup `psp_template` at https://github.com/neonexchange/psp_template.git.

2. Create a virtual environment and install requirements
```
$ cd psp_template/
psp_template$ python3.6 -m venv venv
psp_template$ source venv/bin/activate
(venv) psp_template$ sudo pip install -r requirements.txt 
... wait for a while
(venv) psp_template$ 

```


3. If you intend to use Postgres, create a database
```
(venv) psp_template$ psql
psql (9.x.x)
Type "help" for help.

thomassaunders=# create database psp;
thomassaunders=# create database psp;
CREATE DATABASE
thomassaunders=# \q
```

4. If you want to use `sqlite3` instead, edit `neopsp/settings.py` database settings to look similar to this:
```
DATABASES = {
#    'default': {
#        'ENGINE': 'django.db.backends.postgresql_psycopg2',
#        'NAME': 'psp',
#    },
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}


```

5. Run migrations with `python manage.py migrate`

6. Create a superuser with `python manage.py createsuperuser`

## Run

- you can now start the server with the following command:
- `python manage.py runserver --noreload 8000`
- you should now be able to visit `http://127.0.0.1:8000` in your browser

## Nex Extension

To interact with the system, you will need to download and install the current version of the [NEX Browser Extension](https://github.com/neonexchange/nex-extension-alpha)



## Settings

The following settings should probably be configured to your own content in `nexpsp.settings`

```
CHAIN_DIR = "%s/Data/pspnet" % BASE_DIR # where do you want to sync the chain to

PROTOCOL_FILE = 'protocol.coz.json' # this determines which network you'll run on

PROVIDER_WALLET_FILE = 'your main wallet file'
PROVIDER_WALLET_PASS = 'your main wallet pass'

DWOLLA_KEY = '{Dwolla API Key}'
DWOLLA_SECRET = '{Dwolla API Secret}'

```



## License

- Open-source [MIT](LICENSE.md).
- Main author is [@neonexchange](https://github.com/neonexchange).
