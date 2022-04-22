import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = 490159936

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    level=logging.INFO)

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Отправляет сообщение."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.info(
            'Бот успешно отправил сообщение '
            + message + ' в чат ' + TELEGRAM_CHAT_ID
        )
    except Exception as error:
        logging.error(f'сбой при отправке сообщения в Telegram: {error}')


def get_api_answer(current_timestamp):
    """Запрос к ендпоинту."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except requests.ConnectionError:
        error = (
            f'Error while request:'
            f'endpoint - {ENDPOINT}'
            f'headers - {HEADERS}'
            f'params - {params}'
        )
        raise requests.ConnectionError(error)
    if response.status_code == HTTPStatus.OK:
        return response.json()
    error = f'code API {response.status_code} not equal {HTTPStatus.OK}'
    raise ValueError(error)


def check_response(response):
    """Возвращает список домашних работ."""
    if not response['homeworks']:
        error = f'отсутствует ключ homeworks в ответе: {response}'
        raise NameError(error)
    homework = response['homeworks']
    if not homework:
        error = f'List {homework[0]} is empty'
        raise NameError(error)
    logging.info('Status of homework update')
    return homework[0]


def parse_status(homework):
    """Статус домашней работы."""
    if 'homework_name' not in homework:
        error = f'hw not in API response - {homework}'
        raise KeyError(error)
    if 'status' not in homework:
        error = f'status not in API response - {homework}'
        raise KeyError(error)
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if homework_status not in HOMEWORK_STATUSES:
        error = f'Status - {homework_status} of work not in s.l'
        f'{HOMEWORK_STATUSES}'
        raise KeyError(error)
    verdict = HOMEWORK_STATUSES.get(homework_status)
    logging.info('New status received')
    return f'Изменился статус проверки работы  "{homework_name}". {verdict}'


def check_tokens():
    """Проверка переменных окружения."""
    is_exist = True
    if (PRACTICUM_TOKEN is None
            or TELEGRAM_CHAT_ID is None
            or TELEGRAM_TOKEN is None):
        logging.critical('Одна или более переменных окружения не определены')
        is_exist = False
    return is_exist


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        error = 'нет переменных или как-то так'
        logging.error(error, exc_info=True)
        sys.exit()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time() - 30 * 24 * 60 * 60)
    status = ''
    while True:
        try:
            response = get_api_answer(current_timestamp)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(f'Ошибка при запросе к основному API: {error}')
            time.sleep(RETRY_TIME)
            continue
        try:
            if check_response(response):
                homework = check_response(response)
                message = parse_status(homework)
                if message != status:
                    send_message(bot, message)
                    status = message
            current_timestamp = current_timestamp
            time.sleep(RETRY_TIME)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            if message != status:
                send_message(bot, message)
                status = message
            logging.error(error, exc_info=True)
            time.sleep(RETRY_TIME)
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
