from ..db_session import SqlAlchemyBase
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash
import sqlalchemy


class User(UserMixin, SqlAlchemyBase):
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    username = sqlalchemy.Column(sqlalchemy.String)
    surname = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    email = sqlalchemy.Column(sqlalchemy.String, unique=True, nullable=True)
    password = sqlalchemy.Column(sqlalchemy.String)
    messages_today = sqlalchemy.Column(sqlalchemy.Integer, nullable=True, default=0)
    verification = sqlalchemy.Column(sqlalchemy.Boolean, default=False)
    last_message_time = sqlalchemy.Column(sqlalchemy.DateTime)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def __repr__(self):
        return f'<User> {self.id} {self.surname} {self.name}'