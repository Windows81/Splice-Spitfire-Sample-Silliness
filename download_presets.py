import requests


def download(preset: str):
    headers = {
        'X-Client-Id': '69',
        'Content-Type': 'application/json',
    }

    json_data = {
        'build_id': 215,
        'encryption_key': 'ANCQ49-DCJB4E-JMLW53-LMMR54-MKNM52-PGRD55-SGTW4D-TCM045-4E5400',
        'preset_ids': [preset],
    }

    response = requests.post(
        'https://instrument-api.splice.com/api/v2/hurricane/preset-installations',
        headers=headers,
        json=json_data,
    )


if __name__ == '__main__':
    download('2YPMNPRLzau6iEybXi7GBb')
