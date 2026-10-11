FROM kalilinux/kali-rolling

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        bash \
        dnsutils \
        tcpdump \
        iproute2 \
        iputils-ping \
        procps && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /lab

CMD ["sleep", "infinity"]
