FROM kalilinux/kali-rolling

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        bind9 \
        bind9-utils \
        dnsutils \
        tcpdump \
        iproute2 \
        iputils-ping \
        procps && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY named.conf /etc/bind/named.conf.lab
COPY db.lab.test /etc/bind/db.lab.test

RUN named-checkconf /etc/bind/named.conf.lab && \
    named-checkzone lab.test /etc/bind/db.lab.test

EXPOSE 53/udp
EXPOSE 53/tcp

CMD ["named", "-g", "-c", "/etc/bind/named.conf.lab"]
