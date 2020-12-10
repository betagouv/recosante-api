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