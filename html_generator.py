import json

from mako.template import Template
from json2html import *


def main():
    html_template = Template(filename='template/index.html')
    with open('collector.json') as file:
        data = json.load(file)
    table = json2html.convert(data['media'])
    html = html_template.render(table=table)
    with open('collector.html', 'w+', encoding='utf-8') as file:
        file.write(html)


if __name__ == '__main__':
    main()