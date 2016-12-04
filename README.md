### Config

Copy env-sample to .env and set the variables

```bash
$ cp env-sample .env
```

### Database Migration

**First time use:**

```bash
$ python db_manage.py db init
```
this will create the migration folder with all the information.

**Next time uses:**

```bash
$ python db_manage.py db migrate
$ python db_manage.py db upgrade
```
The first command compares the models.py with the version on the database and write down the migration rule. The second command upgrade the migration to the DB.

### Running

```bash
$ python app.py
```
