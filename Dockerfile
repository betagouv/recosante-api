FROM jekyll/jekyll:3.8

RUN mkdir /ecosante/
WORKDIR /ecosante/
COPY ./ .
RUN chmod -R o+w .

RUN jekyll build

RUN mv _site/base.html ecosante/templates/base.html

FROM python:3.8
RUN apt update && apt install -y --no-install-recommends locales; rm -rf /var/lib/apt/lists/*; sed -i '/^#.* fr_FR.UTF-8 /s/^#//' /etc/locale.gen; locale-gen

WORKDIR /ecosante/
COPY --from=0 /ecosante/ .

RUN pip3 install -r requirements.txt
RUN pip3 install uwsgi
RUN flask startup

EXPOSE 8080

CMD ["uwsgi", "wsgi.ini"]