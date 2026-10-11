FROM kalilinux/kali-rolling

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y python3-pip \
    && apt-get install -y --no-install-recommends \
        bash \
        dnsutils \
        tcpdump \
        iproute2 \
        iputils-ping \
	python3-scapy \
        procps && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /lab
COPY script.py /lab/script.py
RUN chmod 0755 /lab/script.py
CMD ["sleep", "infinity"]
