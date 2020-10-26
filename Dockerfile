FROM python:3.8
RUN apt update && apt install -y --no-install-recommends locales; rm -rf /var/lib/apt/lists/*; sed -i '/^#.* fr_FR.UTF-8 /s/^#//' /etc/locale.gen; locale-gen
RUN apt-get install nodejs npm
RUN npm install -g yarn

RUN mkdir /ecosante/
WORKDIR /ecosante/
COPY ./ .

RUN yarn install
RUN yarn global add node-sass rollup

RUN pip3 install .
RUN pip3 install uwsgi
RUN flask assets build

EXPOSE 8080

CMD ["./startup.sh"]
