FROM ubuntu:20.04

RUN apt-get update && \
    apt-get install -y \
      python3 \
      python3-pip \
      ruby \
      ruby-dev \
      build-essential \
      zlib1g-dev \
      libpq-dev


#Bug de ruby voir https://github.com/rubygems/rubygems/issues/3269
ENV DEBIAN_DISABLE_RUBYGEMS_INTEGRATION=1
RUN gem update --system
RUN gem install bundler

RUN mkdir ecosante
WORKDIR /ecosante
COPY ./ /ecosante

RUN bundle install

RUN ./build.sh

RUN pip3 install -r requirements.txt
RUN pip3 install uwsgi

EXPOSE 8080

CMD uwsgi --ini wsgi.ini