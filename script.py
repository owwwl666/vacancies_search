import requests
from itertools import count
from environs import Env
from terminaltables import AsciiTable

LANGUAGES = [
    "JavaScript",
    "Java",
    "Python",
    "Ruby",
    "PHP",
    "C++",
    "C#",
    "1C",
]


def displays_results_table(vacancy_research, table_title):
    """Выводит результаты исследования вакансий в виде таблицы."""
    table_columns = [("Язык программирования",
                      "Вакансий найдено", "Вакансий обработано",
                      "Средняя зарплата")
                     ]
    for language in vacancy_research:
        table_columns.append(
            (language, vacancy_research[language]["vacancies_found"],
             vacancy_research[language]["vacancies_processed"],
             vacancy_research[language]["average_salary"]
             )
        )

    summary_table = AsciiTable(table_columns, table_title)

    print(summary_table.table)


def process_pages_vacancies(params, predict_rub_salary, total_vacancies, url, headers):
    """Обрабатывает несколько страниц с вакансиями.

    В виде словаря возвращает:
    average_salary -- среднюю зарплату по обработанным вакансиям
    vacancies_found -- количество ваканасий
    vacancies_processed -- количество обработанных вакансий
    """
    pages_processed = []
    salaries = []
    vacancies_processed = []
    for page in count(0):
        params |= {"page": page}
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        pages_processed.append(response.json())
        if page == 3:
            break

    for page in pages_processed:
        salaries_page, vacancies_processed_page = predict_rub_salary(page)
        salaries.extend(salaries_page)
        vacancies_processed.append(vacancies_processed_page)
    average_salary = int(sum(salaries) / len(salaries)) \
        if salaries else None
    vacancies_processed = sum(vacancies_processed)
    vacancies_found = pages_processed[0][total_vacancies]

    return {
        "average_salary": average_salary,
        "vacancies_found": vacancies_found,
        "vacancies_processed": vacancies_processed,
    }


def predict_rub_salary_hh(page):
    """Обрабатывает одну страницу с вакансиямм на hh.ru.

    Возвращает кортеж в виде:
    salaries -- список со всеми зарплатами со страницы
    vacancies_processed -- количество обработанных вакансий на одной странице
    """
    vacancies = page["items"]
    salaries = []
    vacancies_processed = 0
    for vacancy in vacancies:
        salary = vacancy["salary"]
        if not salary or salary["currency"] != "RUR":
            continue
        else:
            salary_from, salary_to = salary["from"], salary["to"]
            if not salary_from:
                expected_salary = salary_to * 0.8
            elif not salary_to:
                expected_salary = salary_from * 1.2
            else:
                expected_salary = (salary_from + salary_to) / 2

            salaries.append(expected_salary)
            vacancies_processed += 1

    return salaries, vacancies_processed


def predict_rub_salary_sj(page):
    """Обрабатывает одну страницу с вакансиямм на superjob.ru.

    Возвращает кортеж в виде:
    salaries -- список со всеми зарплатами со страницы
    vacancies_processed -- количество обработанных вакансий на одной странице
    """
    vacancies = page["objects"]
    salaries = []
    vacancies_processed = 0
    for vacancy in vacancies:
        salary_from, salary_to = vacancy.get("payment_from"), vacancy.get("payment_to")
        if vacancy["currency"] == "rub":
            if not (salary_from and salary_to):
                continue
            if not salary_from and salary_to:
                salaries.append(salary_to * 0.8)
            if not salary_to and salary_from:
                salaries.append(salary_from * 1.2)
            if salary_from and salary_to:
                salaries.append((salary_from + salary_to) / 2)
            vacancies_processed += 1

    return salaries, vacancies_processed


if __name__ == '__main__':

    env = Env()
    env.read_env()

    language_statistics_hh = {}
    language_statistics_sj = {}

    for language in LANGUAGES:
        language_statistics_hh[language] = process_pages_vacancies(
            params={
                "text": f"Программист {language}",
                "area": '1',
                "professional_role": '96',
            },
            predict_rub_salary=predict_rub_salary_hh,
            total_vacancies="found",
            url='https://api.hh.ru/vacancies/',
            headers={}
        )

        language_statistics_sj[language] = process_pages_vacancies(
            params={
                "town": "Москва",
                "keyword": language
            },
            predict_rub_salary=predict_rub_salary_sj,
            total_vacancies="total",
            url='https://api.superjob.ru/2.0/vacancies/',
            headers={'X-Api-App-Id': env.str("SUPERJOB_SECRET_KEY")}
        )

    displays_results_table(language_statistics_hh, "HeadHunter Moscow")
    displays_results_table(language_statistics_sj, "SuperJob Moscow")
