from app import app
import logging
from data.db.db_session import global_init


if __name__ == "__main__":
    logging.basicConfig(filename='record.log', level=logging.DEBUG)
    global_init()
    app.run()