import requests
from pprint import pprint
from itertools import count


def training_all_vacancies(language):
    all_pages = []
    all_average_salaries = []
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
        payload = response.json()
        all_pages.append(payload)
        if page == 3:
            break

    for page in all_pages:
        average_salary_page, vacancies_processed_page = predict_rub_salary(page)
        all_average_salaries.append(average_salary_page)
        vacancies_processed.append(vacancies_processed_page)
    average_salary = int(sum(all_average_salaries) / len(all_average_salaries)) if all_average_salaries else None
    vacancies_processed = sum(vacancies_processed)
    vacancies_found = all_pages[0]["found"]

    return {
        "average_salary": average_salary,
        "vacancies_found": vacancies_found,
        "vacancies_processed": vacancies_processed,
    }


# return all_pages


def predict_rub_salary(jobs):
    vacancies = jobs["items"]
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

    average_salary = int(sum(salaries) / len(salaries)) if len(salaries) > 0 else 0
    vacancies_processed = len(vacancies)
    return average_salary, vacancies_processed


languages = ["JavaScript",
             "Java",
             "Python",
             "Ruby",
             "PHP",
             "C++",
             "C#",
             "1C",
             ]

language_average_salaries = {}

for language in languages:
    language_average_salaries[language] = training_all_vacancies(language)

pprint(language_average_salaries)
