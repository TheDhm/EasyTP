FROM golang:1.14-buster AS easy-novnc-build
WORKDIR /src
RUN go mod init build && \
    go get github.com/geek1011/easy-novnc@v1.1.0 && \
    go build -o /bin/easy-novnc github.com/geek1011/easy-novnc

FROM debian:buster
ENV DEBIAN_FRONTEND=noninteractive
RUN apt update && DEBIAN_FRONTEND=noninteractive

RUN apt-get update -y && \
    apt-get install -y --no-install-recommends openbox tigervnc-standalone-server supervisor gosu && \
    rm -rf /var/lib/apt/lists && \
    mkdir -p /usr/share/desktop-directories

RUN apt-get update -y && \
    apt-get install -y --no-install-recommends lxterminal nano wget openssh-client rsync ca-certificates xdg-utils htop tar xzip gzip bzip2 zip unzip && \
    rm -rf /var/lib/apt/lists

RUN apt-get update -y && \
    apt-get install -y --no-install-recommends default-jre gcc && \
    rm -rf /var/lib/apt/lists

COPY --from=easy-novnc-build /bin/easy-novnc /usr/local/bin/
COPY menu.xml /etc/xdg/openbox/
COPY supervisord.conf /etc/
EXPOSE 8080

RUN groupadd --gid 1000 app && \
    useradd --home-dir /data --shell /bin/bash --uid 1000 --gid 1000 app && \
    mkdir -p /data
RUN apt update && \
	apt install -y python3-pip python3-pyqt5 python3-pyqt5.qtsvg python3-pyqt5.qtwebsockets qemu qemu-kvm qemu-utils libvirt-clients libvirt-daemon-system virtinst wireshark xtightvncviewer apt-transport-https ca-certificates curl gnupg2 software-properties-common && \
	apt install -y telnet xterm && \
	pip3 install gns3-server && \
	pip3 install gns3-gui && \
	curl -fsSL https://download.docker.com/linux/debian/gpg | apt-key add - && \
	add-apt-repository  "deb [arch=amd64] https://download.docker.com/linux/debian  $(lsb_release -cs) stable edge" && \
	echo "deb http://ppa.launchpad.net/gns3/ppa/ubuntu bionic main" >>  /etc/apt/sources.list && \
	echo "deb-src http://ppa.launchpad.net/gns3/ppa/ubuntu bionic main" >>  /etc/apt/sources.list && \
	apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv F88F6D313016330404F710FC9A2FD067A2E3EF7B && \
	apt-get update && \
	apt install -y dynamips ubridge && \
	chown -R root /usr/bin && \
	chown -R app /usr/bin && \
	usermod -aG sudo app && \
	usermod -aG sudo root && \
	usermod -aG ubridge app && \
	usermod -aG kvm app && \
	usermod -aG libvirt app && \
	wget https://www.w7cloud.com/GNS3-IOS/c7200-jk9s-mz.124-13b.bin
	
VOLUME /data

RUN mkdir -p /home/.vnc

CMD ["sh", "-c", "chown app:app /data /dev/stdout && echo ${VNC_PW} | tigervncpasswd -f > /home/.vnc/passwd && exec gosu app supervisord"]
