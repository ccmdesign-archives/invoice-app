# Invoice App

## Development environment (macOS Sierra)

1. Download and install the [PostgresSQL App](http://postgresapp.com/).

2. Create and activate a virtualenv.
```
virtualenv invoice
```
```
source invoice/bin/activate
```

3. Update the `PATH` variable (Add this line to the `activate` script):
```
export PATH="/Applications/Postgres.app/Contents/Versions/latest/bin:$PATH"
```

4. Clone the repo:
```
git clone https://github.com/ccmdesign/invoice-app.git
```

5. Go to the project's folder:
```
cd invoice-app
```

6. Copy env-sample to .env and set the variables:
```
cp env-sample .env
```

**The next commands assume that your virtualenv is activated.**

7. Install the dependencies:
```
pip install -r requirements.txt
```

9. Setup the database:
```
python db_manage.py db init
```
```
python db_manage.py db migrate
```
```
python db_manage.py db upgrade
```

10. Run the local server:
```
python app.py
```
