# django-taxrates
Sales tax rates app for django based on http://www.taxrates.com/


# Usage

## Install the App

```
pip install -e git+git://github.com/inabhi9/django-taxrates.git#egg=taxrates
```

Add `taxrates` app into your django setting file

    INSTALLED_APPS = (
        ...,
        'taxrates'
        ...
    )

## Run migration

    ./manage.py migrate

## Import the data
This is the management command that downloads the data from the taxrates.com and import into the
database.

    ./manage.py taxrates --import=all

Run `./manage.py taxrates -h` for help
