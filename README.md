# Invoice App

## Development environment (macOS Sierra)

1. Follow the official instructions to install [MongoDB](https://docs.mongodb.com/master/tutorial/install-mongodb-on-os-x/)

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

1. Run the local server:
    ```
    python app.py
    ```
