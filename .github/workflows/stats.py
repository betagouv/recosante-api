#!/usr/bin/env python3
import sys
import requests
import csv
from ruamel.yaml import YAML

def make_dict(mois, line):
    index_titre = mois.index('')
    index_total = mois.index('Total')
    index_data = index_total + 1

    return {
        'titre': line[index_titre],
        'total': int(line[index_total]),
        'data': [
            {"mois": k, "valeur": int(v)}
            for k, v in zip(mois[index_data:], line[index_data:])
            if v != ''
        ]
    }


if __name__ == '__main__':
    CSV_URL = sys.argv[1]

    with requests.Session() as s:
        r = s.get(CSV_URL)
        r.raise_for_status()

        decoded_content = r.content.decode('utf-8')

    cr = list(csv.reader(decoded_content.splitlines(), delimiter=','))
    yaml = YAML()

    mois = cr[0]
    data = {
            'acquisition': make_dict(mois, cr[2]),
            'actifs': make_dict(mois, cr[3]),
            'sms': make_dict(mois, cr[4]),
            'mails': make_dict(mois, cr[5]),
            'quotidienne': make_dict(mois, cr[6]),
            'mauvaise_qa': make_dict(mois, cr[7])
    }

    with open('_data/stats.yml', 'w') as f:
        yaml.dump(data, f)        
