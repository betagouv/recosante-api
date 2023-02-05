FROM nikolaik/python-nodejs:python3.10-nodejs19
RUN apt update && apt install -y --no-install-recommends locales; rm -rf /var/lib/apt/lists/*; sed -i '/^#.* fr_FR.UTF-8 /s/^#//' /etc/locale.gen; locale-gen

ADD . /code
WORKDIR /code/

RUN chmod +x startup.sh
RUN chmod +x startup_tests.sh

ENV PIP_ROOT_USER_ACTION=ignore
EXPOSE 8080

CMD ["./startup.sh"]
