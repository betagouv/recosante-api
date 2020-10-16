import csv
from io import StringIO

def generate_line(line):
    stringio = StringIO()
    writer = csv.writer(stringio)
    writer.writerow(line)
    v = stringio.getvalue()
    stringio.close()
    return v