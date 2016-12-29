# Invoice App

## Development environment (macOS Sierra)

1. Download and install the [PostgresSQL App](http://postgresapp.com/).

1. Open the PostgresSQL App and make sure the server is running.

1. Clone the repo:
    ```
    git clone https://github.com/ccmdesign/invoice-app.git
    ```

1. Go to the project's folder:
    ```
    cd invoice-app
    ```

1. Create and activate a virtualenv.
    ```
    virtualenv venv
    ```
    ```
    source venv/bin/activate
    ```

1. Update the `PATH` variable (Add this line to the `./venv/bin/activate` script):
    ```
    export PATH="/Applications/Postgres.app/Contents/Versions/latest/bin:$PATH"
    ```

1. Copy env-sample to .env and set the variables:
    ```
    cp env-sample .env
    ```

    **The next commands assume that your virtualenv is activated.**

1. Install the dependencies:
    ```
    pip install -r requirements.txt
    ```

1. Create the database:
    ```
    createdb invoice
    ```

1. Setup the database:
    ```
    python db_manage.py db init
    ```
    ```
    python db_manage.py db migrate
    ```
    ```
    python db_manage.py db upgrade
    ```

1. Run the local server:
    ```
    python app.py
    ```
