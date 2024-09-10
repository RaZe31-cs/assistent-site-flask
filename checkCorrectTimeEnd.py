from datetime import datetime, timedelta
from data.db.db_session import create_session
from data.db.models.usersTest import UserTest


def main():
    nowDate = datetime.now()
    with create_session() as session:
        users = session.query(UserTest).all()

        for user in users:
            if user.time_end <= nowDate:
                session.delete(user)
                session.commit()




if __name__ == '__main__':
    main()