import csv
from io import StringIO

def generate_line(line):
    if not type(line) is list:
        line = list(line)
    stringio = StringIO()
    writer = csv.writer(stringio)
    writer.writerow(line)
    v = stringio.getvalue()
    stringio.close()
    return v

def convert_boolean_to_oui_non(value):
    return "Oui" if value else "Non"

def oxford_comma(items):
    if not items:
        return
    length = len(items)
    if length == 0:
        return
    elif length == 1:
        return items[0]
    elif length == 2:
        return '{} et {}'.format(*items)
    else:
        return '{}, et {}'.format(', '.join(items[:-1]), items[-1])

def display_check(check):
    return "✅" if check else "❌"