from piipod.logger import logger
logger.setLevel(5)

from piipod import app, db, debug, port
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


def run(app, with_tornado=False):
    from tornado.wsgi import WSGIContainer
    from tornado.httpserver import HTTPServer
    from tornado.ioloop import IOLoop

    # create database
    db.create_all()
    print('[OK] Database creation complete.')

    if with_tornado:
        http_server = HTTPServer(WSGIContainer(app))
        http_server.listen(port)
        IOLoop.instance().start()
    else:
        app.run(host='0.0.0.0', port=port, debug=debug)


parser = argparse.ArgumentParser(description='Small manager for this queue application.')
parser.add_argument('-db', '--database', type=str,
                   help='The database script to run',
                   choices=('create', 'refresh'))
parser.add_argument('-t', '--tornado', action='store_const', const=True,
                    default=False, help='launch with tornado')


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
    elif args.tornado:
        run(app, with_tornado=True)
    else:
        run(app)
