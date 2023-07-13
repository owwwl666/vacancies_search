import requests
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


def process_pages_vacancies(params, predict_rub_salary, total_vacancies, url, headers, vacancies, total_pages):
    """Обрабатывает несколько страниц с вакансиями.

    В виде словаря возвращает:
    average_salary -- среднюю зарплату по обработанным вакансиям
    vacancies_found -- количество ваканасий
    vacancies_processed -- количество обработанных вакансий
    """
    pages_processed = []
    salaries = []
    vacancies_processed = []
    page = 0
    while True:
        params |= {"page": page}
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        page_vacancies = response.json()
        pages_processed.append(page_vacancies)
        pages = page_vacancies[total_pages]
        page += 1
        if page >= pages or not pages:
            break

    for page in pages_processed:
        one_page_salaries, one_page_vacancies_processed = predict_rub_salary(page[vacancies])
        salaries.extend(one_page_salaries)
        vacancies_processed.append(one_page_vacancies_processed)
    average_salary = int(sum(salaries) / len(salaries)) \
        if salaries else None
    vacancies_found = pages_processed[0].get(total_vacancies)
    vacancies_processed = sum(vacancies_processed)

    return {
        "average_salary": average_salary,
        "vacancies_found": vacancies_found,
        "vacancies_processed": vacancies_processed,
    }


def predict_rub_salary_hh(vacancies_page):
    """Обрабатывает одну страницу с вакансиямм на hh.ru.

    Возвращает кортеж в виде:
    salaries -- список со всеми зарплатами со страницы
    vacancies_processed -- количество обработанных вакансий на одной странице
    """
    vacancies = vacancies_page
    salaries = []
    vacancies_processed = 0
    for vacancy in vacancies:
        salary = vacancy.get("salary")
        if not salary or salary["currency"] != "RUR":
            continue
        else:
            salary_from, salary_to = salary["from"], salary["to"]
            salaries.append(predict_salary(salary_from, salary_to))
            vacancies_processed += 1

    return salaries, vacancies_processed


def predict_rub_salary_sj(vacancies_page):
    """Обрабатывает одну страницу с вакансиямм на superjob.ru.

    Возвращает кортеж в виде:
    salaries -- список со всеми зарплатами со страницы
    vacancies_processed -- количество обработанных вакансий на одной странице
    """
    vacancies = vacancies_page
    salaries = []
    vacancies_processed = 0
    for vacancy in vacancies:
        salary_from, salary_to = vacancy.get("payment_from"), vacancy.get("payment_to")
        if vacancy["currency"] == "rub":
            if not (salary_from and salary_to):
                continue
            else:
                salaries.append(predict_salary(salary_from, salary_to))
                vacancies_processed += 1

    return salaries, vacancies_processed


def predict_salary(salary_from, salary_to):
    """Вычисляет среднюю зарплату в вакансии.

    salary_from -- зарплата 'от'
    salary_to -- зарплата 'до'
    """
    if not salary_from:
        salary = salary_to * 0.8
    elif not salary_to:
        salary = salary_from * 1.2
    else:
        salary = (salary_from + salary_to) / 2

    return salary


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
                "per_page": 100,
            },
            predict_rub_salary=predict_rub_salary_hh,
            total_vacancies="found",
            url='https://api.hh.ru/vacancies/',
            headers={},
            vacancies="items",
            total_pages="pages"
        )

        language_statistics_sj[language] = process_pages_vacancies(
            params={
                "town": "Москва",
                "keyword": language,
                "count": 100
            },
            predict_rub_salary=predict_rub_salary_sj,
            total_vacancies="total",
            url='https://api.superjob.ru/2.0/vacancies/',
            headers={'X-Api-App-Id': env.str("SUPERJOB_SECRET_KEY")},
            vacancies="objects",
            total_pages="more"
        )

    displays_results_table(language_statistics_hh, "HeadHunter Moscow")
    displays_results_table(language_statistics_sj, "SuperJob Moscow")
