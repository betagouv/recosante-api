FROM nikolaik/python-nodejs:python3.11-nodejs19
RUN apt update && apt install -y --no-install-recommends locales; rm -rf /var/lib/apt/lists/*; sed -i '/^#.* fr_FR.UTF-8 /s/^#//' /etc/locale.gen; locale-gen

RUN mkdir /recosante-api/
WORKDIR /recosante-api/
COPY ./ .

RUN chmod +x startup.sh

RUN yarn install

RUN pip3 install .

EXPOSE 8080

CMD ["./startup.sh"]
