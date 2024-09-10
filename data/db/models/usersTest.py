from ..db_session import SqlAlchemyBase
from flask_login import UserMixin
import sqlalchemy


class UserTest(UserMixin, SqlAlchemyBase):
    __tablename__ = 'users_tests'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.Text)
    type_access = sqlalchemy.Column(sqlalchemy.Text)
    code = sqlalchemy.Column(sqlalchemy.Text, unique=True)
    thread_id = sqlalchemy.Column(sqlalchemy.Text)
    time_start = sqlalchemy.Column(sqlalchemy.DateTime)
    time_end = sqlalchemy.Column(sqlalchemy.DateTime)


    def __repr__(self):
        return f'<User> {self.id} {self.type_access} {self.code}'