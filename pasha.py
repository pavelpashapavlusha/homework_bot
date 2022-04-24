def main():
    """Основная логика работы бота."""
    if not check_tokens():
        message = 'Отсутствуют необходимые переменные окружения'
        logger.critical(message)
        sys.exit()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time() - 30 * 24 * 60 * 60)
    send_message_error = {}
    while True:
        try:
            response = get_api_answer(current_timestamp)
        except Exception as error:
            message = f'Недоступность эндпоига, {error}'
            logger.error(message)
            chek_send_message_error(bot, message, send_message_error)
            time.sleep(RETRY_TIME)
            current_timestamp = int(time.time())
            continue
        try:
            homeworks_list = check_response(response)
        except Exception as error:
            message = f'API не корректен, {error}'
            logger.error(message)
            chek_send_message_error(bot, message)
            time.sleep(RETRY_TIME)
            current_timestamp = int(time.time())
            continue
        try:
            for numwork in range(0, len(homeworks_list)):
                verdict_status = parse_status(homeworks_list[numwork])
                send_message(bot, verdict_status)
        except DebugHomeworkStatus as error:
            message = (f'Cтатус домашней "{error}" '
                       f'работы, не изменился')
            logger.debug(message)
        except Exception as error:
            message = (f'Ошибка проверка статуса '
                        f'домашней работы, {error}')
            logger.error(message)
            chek_send_message_error(bot, message)
        time.sleep(RETRY_TIME)
        current_timestamp = int(time.time())
        send_message_error = {}
