import random
import string
from openai import OpenAI
from data.db.db_session import create_session
from data.db.models.users import User
from dotenv import dotenv_values
from datetime import datetime, timedelta
from data.db.models.usersTest import UserTest
from data.db.models.assistents import Assistent
import pytz


config = dotenv_values(".env")

api_key = config["OPENAI_API_KEY"]
client = OpenAI(api_key=api_key)


def new_user(password, username):
    sess = create_session()
    user = User(username=username)
    user.set_password(password=password)
    sess.add(user)
    sess.commit()
    sess.close()
    

def reqChatGpt(message):
    response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": message}],
                max_tokens=150
            )
    return response.choices[0].message.content.strip()



def currentUser(userId) -> User:
    sess = create_session()
    user = sess.query(User).filter(userId == User.id).first()
    sess.close()
    return user


def updateUser(userId, **kwargs) -> bool:
    try:
        sess = create_session()
        user = sess.query(User).filter(userId == User.id)
        user.update(kwargs)
        sess.commit()
        sess.close()
        return True, None
    except Exception as e:
        return False, e





def generate_code(length=6):
    return ''.join(random.choices(string.digits, k=length))




def generate_random_code(length=10):
    characters = string.ascii_letters + string.digits
    random_code = ''.join(random.choice(characters) for _ in range(length))
    return random_code


def get_all_users():
    with create_session() as sess:
        return sess.query(UserTest).all()
    

def saveUser(name, type_access, code, thread_id):
    with create_session() as sess:
        dateStart = datetime.now(tz=pytz.timezone('Asia/Irkutsk'))
        dateEnd = dateStart + timedelta(hours=2)
        user = UserTest(name=name, type_access=type_access, code=code, thread_id=thread_id, time_start=dateStart, time_end=dateEnd)
        sess.add(user)
        sess.commit()


def saveAssistent(api, asstId, type_access):
    now = datetime.now(tz=pytz.timezone('Asia/Irkutsk'))
    with create_session() as sess:
        asst = Assistent(api=api, asst_id=asstId, type_access=type_access, date_created=now)
        sess.add(asst)
        sess.commit()


def check_code_exists(code):
    with create_session() as sess:
        return sess.query(UserTest).filter(UserTest.code == code).count() > 0
    

def newMessageTxt(code):
    with create_session() as sess:
        user = sess.query(UserTest).filter(UserTest.code == code).first()
        if user:
            dateStart = user.time_start
            dateEnd = user.time_end
            message = f'Привет, это ваш код доступа к генератору сообщений.\n\nКод: {code}\n\nДоступен с {dateStart.strftime("%d.%m.%Y %H:%M")} до {dateEnd.strftime("%d.%m.%Y %H:%M")}.'
            with open(f'messages/{code}.txt', 'w') as file:
                file.write(message)



def get_all_assistents():
    with create_session() as sess:
        return sess.query(Assistent).all()
    
# def get_by_id_assistent(asstId):
#     with create_session() as sess:
#         return sess.query(Assistent).filter(Assistent.asst_id == asstId).first()
    

def get_by_code_user(code):
    with create_session() as sess:
        return sess.query(UserTest).filter(UserTest.code == code).first()
    
# def get_free_type_access_assistents():

def getAsstMetaInfoByTypeAccess(typeAccess):
    with create_session() as sess:
        asst = sess.query(Assistent).filter(Assistent.type_access == typeAccess).first()
        if asst is None:
            raise ValueError('No free assistant found')
    return asst.api, asst.asst_id


def newThreadId(typeAccess):
    api_key, _ = getAsstMetaInfoByTypeAccess(typeAccess)
    with OpenAI(api_key=api_key) as client2:
        thread = client2.beta.threads.create()
    return thread.id


def getmessageFromOpenAI(message, typeAccess, thread_id):
    api_key, asst_id = getAsstMetaInfoByTypeAccess(typeAccess)
    with OpenAI(api_key=api_key) as client2:
        messageFromOpenAi = client2.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=message
        )
        run = client2.beta.threads.runs.create_and_poll(
            thread_id=thread_id,
            assistant_id=asst_id,
        )
        if run.status == 'completed': 
            messages = client2.beta.threads.messages.list(
                thread_id=thread_id
            )
            return messages.data[0].content[0].text.value
        else:
            return run.status
        


def writeDialogMessage(msgUser, msgAssistant, timeRes, code, error=None):
    now = datetime.now(tz=pytz.timezone('Asia/Irkutsk'))
    with open(f'messages/{code}.txt', 'a') as file:
        file.write(f'\n\nTime[Irkutsk]: {now}\nUserMessage: {msgUser}\nAssistantMessage: {msgAssistant}\nTimeRes[Seconds]: {timeRes}\n')
        if error:
            file.write(f'Error: {error}\n')

