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
            "town": "Москва",
            "keyword": language
        }
        response = requests.get('https://api.superjob.ru/2.0/vacancies/', headers={
            'X-Api-App-Id': 'v3.r.137668029.6bddc51f228c0e3cafc1b3d27f9f5b9e211619de.f8cb577a0fc2a43dfbd70de44a34042caedd1f1b'},
                                params=params)
        response.raise_for_status()
        payload = response.json()
        all_pages.append(payload)
        if page == 3:
            break

    for page in all_pages:
        average_salary_page, vacancies_processed_page = predict_rub_salary(page)
        all_average_salaries.append(average_salary_page)
        vacancies_processed.append(vacancies_processed_page)
    all_average_salaries = [salary for salary in all_average_salaries if salary]
    average_salary = int(sum(all_average_salaries) / len(all_average_salaries)) if all_average_salaries else None
    vacancies_processed = sum(vacancies_processed)
    vacancies_found = all_pages[0]["total"]

    return {
        "average_salary": average_salary,
        "vacancies_found": vacancies_found,
        "vacancies_processed": vacancies_processed,
    }


def predict_rub_salary(jobs):
    vacancies = jobs["objects"]
    salaries = []
    for vacancy in vacancies:
        salary_from, salary_to = vacancy.get("payment_from"), vacancy.get("payment_to")
        if not (salary_from and salary_to):
            continue
        if not salary_from and salary_to:
            salaries.append(salary_to * 0.8)
        if not salary_to and salary_from:
            salaries.append(salary_from * 1.2)
        if salary_from and salary_to:
            salaries.append((salary_from + salary_to) / 2)

    average_salary = int(sum(salaries) / len(salaries)) if salaries else None
    vacancies_processed = len(vacancies)
    # return {
    #     "average_salary": average_salary,
    #     "vacancies_found": jobs["total"],
    #     "vacancies_processed": len(jobs["objects"])
    # }
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
    # pprint(response)
    # break
pprint(language_average_salaries)
