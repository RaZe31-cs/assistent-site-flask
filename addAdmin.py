from datetime import datetime, timedelta
from data.db.db_session import create_session, global_init
from data.db.models.admins import Admin
from werkzeug.security import generate_password_hash




def main(username, password):
    with create_session() as session:
        admin = Admin(username=username, password=generate_password_hash(password))
        session.add(admin)
        session.commit()
    print('Admin created')

if __name__ == '__main__':
    global_init()
    username = 'adminPavel'
    password = "Ees63]b9Fei"
    main(username, password)