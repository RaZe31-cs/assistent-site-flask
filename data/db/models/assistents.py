from ..db_session import SqlAlchemyBase
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash
import sqlalchemy


class Assistent(UserMixin, SqlAlchemyBase):
    __tablename__ = 'assistents'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    api = sqlalchemy.Column(sqlalchemy.Text)
    asst_id = sqlalchemy.Column(sqlalchemy.Text)
    type_access = sqlalchemy.Column(sqlalchemy.Text, unique=True)
    date_created = sqlalchemy.Column(sqlalchemy.DateTime)
