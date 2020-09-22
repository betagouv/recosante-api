FROM jekyll/jekyll:3.8

RUN mkdir /ecosante/
WORKDIR /ecosante/
COPY ./ .
RUN chmod -R o+w .

RUN jekyll build

RUN mv _site/base.html ecosante/templates/base.html

FROM python:3.8

WORKDIR /ecosante/
COPY --from=0 /ecosante/ .

RUN pip3 install -r requirements.txt
RUN pip3 install uwsgi

EXPOSE 8080

CMD ["uwsgi", "wsgi.ini"]