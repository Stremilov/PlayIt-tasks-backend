base_bad_response_for_endpoints_of_task = {
    401: {
        "description": "Пользователь не авторизован",
        "content": {
            "application/json": {
                "examples": {
                    "not_authorized": {
                        "summary": "JWT-токен отсутствует или невалиден",
                        "value": {"detail": "Не авторизован"},
                    }
                }
            }
        },
    },
    404: {
        "description": "Пользователь не найден",
        "content": {
            "application/json": {
                "examples": {
                    "user_not_found": {
                        "summary": "Задача не найдена в базе данных",
                        "value": {"detail": "Пользователь не найден"},
                    }
                }
            }
        },
    },
    500: {
        "description": "Внутренняя ошибка сервера",
        "content": {
            "application/json": {
                "examples": {
                    "unexpected_error": {
                        "summary": "Неожиданная ошибка",
                        "value": {
                            "detail": "Произошла непредвиденная ошибка: <тип ошибки>"
                        },
                    }
                }
            }
        },
    },
}

bad_responses_autocheck = {
    404: {
        "description": "Задание с указанным ID не найдено в Excel-файле."
    }
}
