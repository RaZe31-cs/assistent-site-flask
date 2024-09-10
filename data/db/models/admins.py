from ..db_session import SqlAlchemyBase
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash
import sqlalchemy


class Admin(UserMixin, SqlAlchemyBase):
    __tablename__ = 'admins'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    username = sqlalchemy.Column(sqlalchemy.String)
    password = sqlalchemy.Column(sqlalchemy.String)


    def __repr__(self):
        return f'<User> {self.id} {self.username}'