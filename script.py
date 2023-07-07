import requests
from pprint import pprint


def predict_rub_salary(jobs):
    vacancies = jobs["items"]
    all_salary = []
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

            all_salary.append(expected_salary)

    average_salary = int(sum(all_salary) / len(all_salary))
    vacancies_processed = len(vacancies)
    vacancies_found = jobs["found"]

    return {
        "average_salary": average_salary,
        "vacancies_processed": vacancies_processed,
        "vacancies_found": vacancies_found
    }


languages = ["JavaScript",
             "Java",
             "Python",
             "Ruby",
             "PHP",
             "C++",
             "C#",
             "Go",
             ]

language_average_salaries = {}
for language in languages:
    params = {
        "text": language,
        "area": '1',
        "professional_role": '96',
    }
    response = requests.get('https://api.hh.ru/vacancies/', params=params).json()

    language_average_salaries[language] = predict_rub_salary(response)

pprint(language_average_salaries)
