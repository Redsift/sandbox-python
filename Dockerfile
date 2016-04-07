FROM ubuntu:15.10
MAINTAINER Deepak Prabhakara email: deepak@redsift.io version: 1.1.101

ENV NANO_MSG=0.8-beta

ENV PYTHONUNBUFFERED=1

ENV SIFT_ROOT="/run/dagger/sift" IPC_ROOT="/run/dagger/ipc" SIFT_JSON="sift.json"
LABEL io.redsift.dagger.init="/usr/bin/redsift/install.py" io.redsift.dagger.run="/usr/bin/redsift/bootstrap.py"

# Fix for ubuntu to ensure /etc/default/locale is present
RUN update-locale

RUN export DEBIAN_FRONTEND=noninteractive && \ 
  apt-get update && \
	apt-get upgrade -y && \
	apt-get install -y \
  curl autoconf libtool make && \
  apt-get clean -y && \
	rm -rf /root/.pip/cache/* /tmp/pip* && \
  rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN cd /tmp && curl -L https://github.com/nanomsg/nanomsg/archive/$NANO_MSG.tar.gz | tar xz && \
  cd /tmp/nanomsg-$NANO_MSG && sh autogen.sh && ./configure && make && make check && make install && \
  rm -rf /tmp/nanomsg-$NANO_MSG

# Update .so cache
RUN ldconfig

RUN export DEBIAN_FRONTEND=noninteractive && \ 
  apt-get update && \
	apt-get upgrade -y && \
	apt-get install -y \
	build-essential git pkg-config \
  python2.7-dev python2.7 python-pip && \
  apt-get clean -y && \
	rm -rf /root/.pip/cache/* /tmp/pip* && \
  rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

COPY root /
COPY vendor /vendor

RUN cd /vendor/nanomsg-python && python setup.py install

RUN pip install -r /usr/bin/redsift/requirements.txt

VOLUME /run/dagger/sift

WORKDIR /run/dagger/sift

ENTRYPOINT ["/usr/bin/python"]
