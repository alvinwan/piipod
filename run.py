from piiipod.logger import logger
logger.setLevel(0)

from piiipod import app, db, debug
from sqlalchemy.exc import OperationalError
import argparse
import os


def db_refresh():
    """Refresh database"""
    db.drop_all()
    db_create()


def db_create():
    """Create database"""
    try:
        db.create_all()

    except OperationalError:
        raise UserWarning('It looks like your MySQL server hasn\'t been started yet.')


def run(app):
    db_create()
    logger.info('[OK] Database creation complete.')
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=debug)


parser = argparse.ArgumentParser(description='Small manager for this queue application.')
parser.add_argument('-s', '--settings', type=str,
                   help='Whether or not to override default settings',
                   choices=('default', 'override'))
parser.add_argument('-db', '--database', type=str,
                   help='The database script to run',
                   choices=('create', 'refresh'))


if __name__ == "__main__":
    args = parser.parse_args()
    if args.database == 'create':
        db_create()
        print("""---

[OK] Database creation complete.
Use 'make run' to launch server.
    """)
    elif args.database == 'refresh':
        db_refresh()
        print("""---

[OK] Database refresh complete.
Use 'make run' to launch server.
    """)
    else:
        run(app)
