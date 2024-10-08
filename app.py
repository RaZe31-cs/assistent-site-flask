import time
from flask import Flask, jsonify, render_template, redirect, url_for, request, session, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, Email, EqualTo, ValidationError, DataRequired
from data.db.db_session import global_init, create_session
from openai import OpenAI
from datetime import datetime, timedelta
from data.db.models.users import User
from data.db.models.assistents import Assistent
from data.db.models.admins import Admin
from data.db.models.usersTest import UserTest
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import dotenv_values
from utils import *
from flask_mail import Mail, Message
import logging

config = dotenv_values(".env")

app = Flask(__name__)
app.config['SECRET_KEY'] = config['FLASK_SECRET_KEY']
app.config['MAIL_SERVER'] = config['MAIL_SERVER']
app.config['MAIL_PORT'] = config['MAIL_PORT']
app.config['MAIL_USE_TLS'] = config['MAIL_USE_TLS']
app.config['MAIL_USE_SSL'] = config['MAIL_USE_SSL']
app.config['MAIL_USERNAME'] = config["MAIL_USERNAME"]
app.config['MAIL_PASSWORD'] = config["MAIL_PASSWORD"]
app.config['MAIL_DEFAULT_SENDER'] = config["MAIL_EMAIL"]  # Ваш email
app.config['UPLOAD_FOLDER'] = '/root/gpt-site2/messages'


mail = Mail(app)

verification_codes = {}

logging.basicConfig(format='%(asctime)s;%(levelname)s;%(message)s', filename='log/siteGpt.log', filemode='a', level="INFO")

logging.info('[START]: Site started')

global_init()


def validPressButton(form, field):
    if session.get('lastTimeSendCode', False) and session['lastTimeSendCode'] + 30 > time.time():
        raise ValidationError(f"Слишком часто, попробуйте через {session['lastTimeSendCode'] + 30 > time.time()}")
    elif not session.get('lastTimeSendCode', False):
        session['lastTimeSendCode'] = time.time()
    # if form.email. == "":
    #     raise ValidationError(f"заполните поле с почтой")
        


class RegistrationForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[InputRequired(), Length(min=2, max=20)])
    email = StringField('Почта', validators=[InputRequired(), Email()])
    password = PasswordField('Пароль', validators=[InputRequired(), Length(min=6, max=60)])
    confirm_password = PasswordField('Подтверждение пароля', validators=[InputRequired(), EqualTo('password')])
    submit = SubmitField('Регистрация')

class LoginForm(FlaskForm):
    email = StringField('Почта', validators=[InputRequired(), Email()])
    password = PasswordField('Пароль', validators=[InputRequired()])
    submit = SubmitField('Войти')

class MessageForm(FlaskForm):
    message = StringField('Сообщение', validators=[InputRequired()])
    submit = SubmitField('Отправить')


class VerificationForm(FlaskForm):
    verification_code = StringField('Verification Code', validators=[DataRequired(), Length(min=6, max=6)])
    submit = SubmitField('Submit')


@app.route('/')
@app.route('/home')
def home():
    sess = create_session()
    if 'user_id' in session:
        session['listMessage'] = []
        user = sess.query(User).filter(User.id==int(session['user_id'])).first()
        messages_today = user.messages_today
        if user.last_message_time is None or datetime.utcnow() - user.last_message_time < timedelta(days=1):
            remaining_messages = 3 - messages_today
        else:
            remaining_messages = 3
            user.messages_today = 0
            user.last_message_time = datetime.utcnow()
            sess.commit()
        sess.close()
        return render_template('home.html', username=user.username, remaining_messages=remaining_messages)
    return redirect(url_for('register'))


@app.route('/verify', methods=['GET', 'POST'])
def verify():
    form = VerificationForm()
    
    if form.validate_on_submit():
        verification_code = form.verification_code.data
        message, statusId = verify_code(verification_code)
        if statusId == 200:
            updateUser(session.get("user_id"), verification=True)
            return redirect(url_for('login'))  # Перенаправление на успешную страницу
        
    return render_template('verification.html', form=form)



def send_code(email):
    logging.info(f'Sending verification code to {email}')
    if not email:
        return {'error': 'Email is required'}, 400

    code = generate_code()
    verification_codes[email] = code

    msg = Message('Your Verification Code', recipients=[email])
    msg.body = f'Your verification code is {code}'
    mail.send(msg)
    logging.info(f'Verification code sent to {email}')

    return {'message': 'Verification code sent'}, 200



def verify_code(code):
    sess = create_session()
    user = sess.query(User).filter(User.id == session.get('user_id', 0)).first()
    email = user.email
    if email not in verification_codes:
        return "Error"
    if verification_codes[email] == code:
        del verification_codes[email]
        logging.info(f'Verification code verified for {email}')
        return jsonify({'message': 'Verification successful'}), 200
    else:
        return jsonify({'error': 'Invalid code'}), 400
    

@app.route('/login', methods=['GET', 'POST'])
def login():
    logging.info('[LOGIN]: User trying to login')
    sess = create_session()
    form = LoginForm()
    if form.validate_on_submit():
        user = sess.query(User).filter(User.email==form.email.data).first()
        sess.close()
        if user and check_password_hash(user.password, form.password.data):
            logging.info(f'User {user.email} logged in')
            session['user_id'] = user.id
            return redirect(url_for('home'))
        else:
            logging.info(f'User {form.email.data} failed to login')
            flash('Войти не удалось. Пожалуйста, проверьте адрес электронной почты и пароль', 'danger')
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    sess = create_session()
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        sess.add(user)
        sess.commit()
        session['user_id'] = user.id
        sess.close()
        flash('Ваш аккаунт был создан! Теперь вам нужно подтвердить почту', 'success')
        send_code(form.email.data)
        logging.info(f'User {form.email.data} registered')
        return redirect(url_for('verify'))
    logging.info("Registration")
    return render_template('register.html', form=form)

@app.route('/logout')
def logout():
    logging.info('[LOGOUT]: User logged out')
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    logging.info('[CHAT]: User trying to chat')
    sess = create_session()
    if 'user_id' not in session:
        logging.info('[CHAT]: User not logged in')
        return redirect(url_for('register'))
    user = sess.query(User).filter(User.id == int(session['user_id'])).first()
    if not user.verification:
        logging.info('[CHAT]: User not verified')
        return redirect(url_for('verify'))
    form = MessageForm()
    if form.validate_on_submit() and user:
        if user.last_message_time is not None and (datetime.utcnow() - user.last_message_time < timedelta(days=1) and user.messages_today >= 3):
            flash("Вы достигли лимита сообщений на сегодня. Зарегистрируйтесь", 'danger')
            logging.info('[CHAT]: User exceeded message limit')
            return redirect(url_for('home'))
        else:
            logging.info(f'[CHAT]: User sent message: {form.message.data}')
            user.messages_today += 1
            user.last_message_time = datetime.utcnow()
            sess.commit()
            chat_response = reqChatGpt(form.message.data)
            logging.info(f'ChatGPT responded with: {chat_response}')
            session['listMessage'] += [{"user": "user", "message": form.message.data}, {"user": "chatgpt", "message": chat_response}]
            flash('Сообщение отправлено!', 'success')
            return render_template('chat.html', form=form, messages=session['listMessage'])
    return render_template('chat.html', form=form)


@app.route('/admin_login', methods=['GET', 'POST'])
def adminLogin():
    logging.info('[ADMIN LOGIN]: Admin trying to login')
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        with create_session() as sess:
            admin = sess.query(Admin).filter(Admin.username == username).first()
            if admin and check_password_hash(admin.password, password):
                logging.info(f'Admin {username} logged in')
                session['admin_id'] = admin.id
                return redirect(url_for('adminPanel'))
            else:
                logging.info(f'Admin {username} failed to login')
                flash('Неверный логин или пароль')
    return render_template('admin_login.html')

@app.route('/admin_settings', methods=['GET', 'POST'])
def adminSettings():
    logging.info('[ADMIN SETTINGS]: Admin trying to access settings')
    if session.get('admin_id', False):
        logging.info('[ADMIN SETTINGS]: Admin accessing settings')
        return render_template('admin_settings.html', assistents=get_all_assistents())
    return redirect(url_for('adminLogin'))

@app.route('/deleteAssistent/<asstId>', methods=['POST'])
def deleteAssistent(asstId):
    logging.info('[ADMIN SETTINGS]: Admin trying to delete assistant')
    if session.get('admin_id', False):
        with create_session() as sess:
            asst = sess.query(Assistent).filter(Assistent.id == asstId).first()
            if asst:
                sess.delete(asst)
                sess.commit()
        logging.info('[ADMIN SETTINGS]: Assistant deleted')
        return render_template('admin_settings.html', assistents=get_all_assistents())
    logging.info('[ADMIN SETTINGS]: Failed to delete assistant')
    return redirect(url_for('adminLogin'))


@app.route('/admin_users', methods=['GET', 'POST'])
def adminUsers():
    logging.info('[ADMIN USERS]: Admin trying to access users')
    if session.get('admin_id', False):
        logging.info('[ADMIN USERS]: Admin accessing users')
        return render_template('admin_users.html', users=sorted(get_all_users(), key=lambda x: x.time_start, reverse=True))
    logging.info('[ADMIN USERS]: Admin failed to access users')
    return redirect(url_for('adminLogin'))


@app.route('/viewMessage/<messageId>', methods=['GET', 'POST'])
def viewMessage(messageId):
    logging.info(f'[VIEW MESSAGE]: Admin check messages with messageId: {messageId}, admin_id: {session.get("admin_id", "")}')
    if session.get('admin_id', False):
        logging.info('[VIEW MESSAGE]: successfully accessed messages')
        return send_from_directory(directory=app.config['UPLOAD_FOLDER'], path=messageId + '.txt')
    logging.info('[VIEW MESSAGE]: Failed to access messages')
    return redirect(url_for('adminLogin'))



@app.route('/admin_panel', methods=['GET', 'POST'])
def adminPanel():
    logging.info('[ADMIN PANEL]: Admin trying to access panel')
    if session.get('admin_id', False):
        logging.info('[ADMIN PANEL]: Successfully accessed panel')
        return render_template('admin_panel.html')
    logging.info('[ADMIN PANEL]: Failed to access panel')
    return redirect(url_for('adminLogin'))


@app.route('/deleteUser/<userId>', methods=['GET', 'POST'])
def deleteUser(userId):
    logging.info(f'[DELETE USER]: Admin trying to delete user with userId: {userId}, admin_id: {session.get("admin_id", "")}')
    if session.get('admin_id', False):
        if request.method == 'POST':
            with create_session() as sess:
                user = sess.query(UserTest).filter(UserTest.id == int(userId)).first()
                if user:
                    sess.delete(user)
                    sess.commit()
            logging.info('[DELETE USER]: User deleted successfully')
            return render_template('admin_users.html', users=get_all_users())
        logging.info('[DELETE USER]: Failed to delete user')
        return 'Удаление пользователя не возможно'
    logging.info('[DELETE USER]: Failed to delete user')
    return redirect(url_for('adminLogin'))



@app.route('/createUser', methods=['GET', 'POST'])
def createUser():
    logging.info(f'[CREATE USER]: Admin trying to create user, admin_id: {session.get("admin_id", "")}')
    if session.get('admin_id', False):
        if request.method == 'POST':
            name = request.form.get('name')
            type_access = request.form.get('type_access')
            # thread_id = newThreadId(type_access)
            thread_id = '1234567890'
            while True:
                code = generate_random_code(length=25)
                if not check_code_exists(code):
                    break
            saveUser(name, type_access, code, thread_id)
            newMessageTxt(code)
            logging.info(f'[CREATE USER]: User created successfully, name: {name}, type_access: {type_access}, code: {code}')
            return render_template('admin_create_user.html', message=f'Пользователь успешно создан! Ниже указан код', code=code, assistents=get_all_assistents())
        return render_template('admin_create_user.html', assistents=get_all_assistents())
    logging.info(f'[CREATE USER]: User created failed')
    return redirect(url_for('adminLogin'))


@app.route('/createAssistent', methods=['GET', 'POST'])
def createAssistent():
    logging.info(f'[CREATE ASSISTANT]: Admin trying to create assistant, admin_id: {session.get("admin_id", "")}')
    if session.get('admin_id', False):
        if request.method == 'POST':
            api = request.form.get('api')
            asstId = request.form.get('asstId')
            type_access = request.form.get('type_access')
            saveAssistent(api, asstId, type_access)
            logging.info(f'[CREATE ASSISTANT]: Assistant created successfully, api: {api}, asstId: {asstId}, type_access: {type_access}')
            return render_template('admin_create_asst.html', message='Ассистент успешно создан!')
        return render_template('admin_create_asst.html')
    logging.info(f'[CREATE ASSISTANT]: Assistant created failed')
    return redirect(url_for('adminLogin'))



@app.route('/putCode', methods=['GET', 'POST'])
def putCode():
    logging.info(f'[PUT CODE]: User trying to put code')
    session['messages'] = []
    if request.method == 'POST':
        code = request.form.get('code')
        with create_session() as sess:
            user = sess.query(UserTest).filter(UserTest.code == code).first()
            if user:
                session['code'] = user.code
                logging.info(f'[PUT CODE]: User put code successfully, code: {code}')
                return redirect(url_for('testingChat'))
            logging.info(f'[PUT CODE]: User failed to put code, code: {code}')
            return render_template('chat_code.html', message='Код не найден')
    return render_template('chat_code.html')
            


@app.route('/testingChat', methods=['GET', 'POST'])
def testingChat():
    startTime = time.time()
    code = session.get('code', False)
    logging.info(f'[TESTING CHAT]: User trying to test chat, code: {code}')
    if not session.get('messages', False):
        logging.info('[TESTING CHAT]: Messages not found, creating new in session')
        session['messages'] = []
    if code:
        user = get_by_code_user(code)
        type_access = user.type_access
        date_created = user.time_start
        if date_created + timedelta(hours=2) < datetime.now():
            logging.info(f'[TESTING CHAT]: User is in trial period, code: {code}')
            return render_template('chat_chat.html', type_access=type_access, messages=session['messages'], errors="Истек срок пробного использования")
        if user is None:
            logging.warning(f'[TESTING CHAT]: User not found in database, code: {code}')
            return redirect(url_for('putCode'))
        if request.method == 'POST':
            message = request.form.get('message', None)
            logging.info(f'[TESTING CHAT]: Message: {message}')
            if message is None or message == '':
                endTime = time.time()
                executionTime = endTime - startTime
                writeDialogMessage(message, "", executionTime, code, error="Empty message")
                return render_template('chat_chat.html', type_access=type_access, messages=session['messages'], errors="Сообщение не может быть пустым")
            if user is None:
                endTime = time.time()
                executionTime = endTime - startTime
                writeDialogMessage(message, "", executionTime, code, error=f"No user by code: {code}")
                return render_template('chat_chat.html', type_access=type_access, messages=session['messages'], errors="Вашего кода нету в базе данных")
            session['messages'].append({'sender': user.name, 'text': message})
            resMessage = getmessageFromOpenAI(message, type_access, thread_id=user.thread_id)
            session['messages'].append({'sender': '@assistant', 'text': resMessage})
            logging.info(f'[TESTING CHAT]: Message sent successfully: {message} -> {resMessage}')
            endTime = time.time()
            executionTime = endTime - startTime
            writeDialogMessage(message, resMessage, executionTime, code)
            return render_template('chat_chat.html', type_access=type_access, messages=session['messages'])
        return render_template('chat_chat.html', messages=session['messages'])
    return redirect(url_for('putCode'))



if __name__ == '__main__':
    app.run(port=5000, host=config["FLASK_HOST"], debug=True)