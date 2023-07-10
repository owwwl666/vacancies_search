import requests
from pprint import pprint
from itertools import count
from environs import Env
from terminaltables import AsciiTable

env = Env()
env.read_env()

languages = ["JavaScript",
             "Java",
             "Python",
             "Ruby",
             "PHP",
             "C++",
             "C#",
             "1C",
             ]


def displays_results_table(vacancy_research, table_title):
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


def handles_pages_vacancies_hh(language):
    pages_processed = []
    salaries = []
    vacancies_processed = []
    for page in count(0):

        params = {
            "page": page,
            "text": f"Программист {language}",
            "area": '1',
            "professional_role": '96',
        }
        response = requests.get('https://api.hh.ru/vacancies/', params=params)
        response.raise_for_status()
        pages_processed.append(response.json())
        if page == 3:
            break

    for page in pages_processed:
        salaries_page, vacancies_processed_page = predict_rub_salary_hh(page)
        salaries.extend(salaries_page)
        vacancies_processed.append(vacancies_processed_page)
    average_salary = int(sum(salaries) / len(salaries)) \
        if salaries else None
    vacancies_processed = sum(vacancies_processed)
    vacancies_found = pages_processed[0]["found"]

    return {
        "average_salary": average_salary,
        "vacancies_found": vacancies_found,
        "vacancies_processed": vacancies_processed,
    }


def predict_rub_salary_hh(page):
    vacancies = page["items"]
    salaries = []
    for vacancy in vacancies:
        salary = vacancy["salary"]
        if salary is None or salary["currency"] != "RUR":
            continue
        else:
            salary_from, salary_to = salary["from"], salary["to"]
            if salary_from is None:
                expected_salary = salary_to * 0.8
            elif salary_to is None:
                expected_salary = salary_from * 1.2
            else:
                expected_salary = (salary_from + salary_to) / 2

            salaries.append(expected_salary)

    vacancies_salary = salaries if salaries else []
    vacancies_processed = page["per_page"]
    return vacancies_salary, vacancies_processed


def handles_pages_vacancies_sj(language):
    pages_processed = []
    salaries = []
    vacancies_processed = []
    for page in count(0):

        params = {
            "page": page,
            "town": "Москва",
            "keyword": language
        }
        response = requests.get('https://api.superjob.ru/2.0/vacancies/', headers={
            'X-Api-App-Id': env.str("SUPERJOB_SECRET_KEY")},
                                params=params)
        response.raise_for_status()
        pages_processed.append(response.json())
        if page == 3:
            break

    for page in pages_processed:
        salaries_page, vacancies_processed_page = predict_rub_salary_sj(page)
        salaries.extend(salaries_page)
        vacancies_processed.append(vacancies_processed_page)
    average_salary = int(sum(salaries) / len(salaries)) \
        if salaries else None
    vacancies_processed = sum(vacancies_processed)
    vacancies_found = pages_processed[0]["total"]

    return {
        "average_salary": average_salary,
        "vacancies_found": vacancies_found,
        "vacancies_processed": vacancies_processed,
    }


def predict_rub_salary_sj(page):
    vacancies = page["objects"]
    salaries = []
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

    vacancies_salary = salaries if salaries else []
    vacancies_processed = len(vacancies)
    return vacancies_salary, vacancies_processed


language_statistics_hh = {}
language_statistics_sj = {}

for language in languages:
    language_statistics_hh[language] = handles_pages_vacancies_hh(language)
    language_statistics_sj[language] = handles_pages_vacancies_sj(language)

displays_results_table(language_statistics_hh, "HeadHunter Moscow")
displays_results_table(language_statistics_sj, "SuperJob Moscow")
