FROM ubuntu:22.04

LABEL org.opencontainers.image.title "MediaCrawl"
LABEL org.opencontainers.image.licenses MIT
LABEL org.opencontainers.image.source https://github.com/opensanctions/mediacrawl

ENV DEBIAN_FRONTEND noninteractive

# build-essential 
RUN apt-get -qq -y update \
    && apt-get -qq -y install locales ca-certificates tzdata curl \
    python3-pip libpq-dev python3-icu python3-psycopg2 python3-cryptography \
    && apt-get -qq -y autoremove \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN localedef -i en_US -c -f UTF-8 -A /usr/share/locale/locale.alias en_US.UTF-8 \
    && ln -fs /usr/share/zoneinfo/Etc/UTC /etc/localtime \
    && dpkg-reconfigure -f noninteractive tzdata \
    && groupadd -g 1000 -r app \
    && useradd -m -u 1000 -s /bin/false -g app app

ENV LANG="en_US.UTF-8" \
    TZ="UTC"

COPY requirements.txt /tmp/requirements.txt
RUN pip3 install -r /tmp/requirements.txt

COPY . /mediacrawl
RUN pip3 install -e /mediacrawl
WORKDIR /mediacrawl

CMD mediacrawl crawl sites.yml