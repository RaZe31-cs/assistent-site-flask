import requests
from dotenv import dotenv_values




config = dotenv_values(".env")


def send_telegram_message(message):
    """Отправляет сообщение в Telegram."""
    url = f'https://api.telegram.org/bot{config["TELEGRAM_FAIL_API_KEY"]}/sendMessage'
    payload = {'chat_id': config['TELEGRAM_FAIL_CHAT_ID'], 'text': message}
    try:
        response = requests.post(url, data=payload)
        if response.status_code != 200:
            logging.error(f"Failed to send message to Telegram: {response.text}")
    except Exception as e:
        logging.error(f"Exception occurred while sending message to Telegram: {e}")



if __name__ == "__main__":
    send_telegram_message("Произошлая ошибка, бот должен перезапуститься, проверьте на сервере командой: systemctl status GptSite")
