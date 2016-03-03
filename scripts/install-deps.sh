#!/bin/sh

set -v

case "$TRAVIS_OS_NAME" in
  linux)
    echo "START LINUX"
    sudo apt-get install ruby
    yes '' | ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/linuxbrew/go/install)"
    sudo apt-get install -y build-essential
    export PATH="$HOME/.linuxbrew/bin:$PATH"
    export MANPATH="$HOME/.linuxbrew/share/man:$MANPATH"
    export INFOPATH="$HOME/.linuxbrew/share/info:$INFOPATH"
    # install deps for OLA
    sudo apt-get install -y libcppunit-dev libcppunit-1.13-0 uuid-dev pkg-config libncurses5-dev libtool autoconf automake g++ libmicrohttpd-dev \
    libmicrohttpd10 protobuf-compiler libprotobuf-lite8 python-protobuf libprotobuf-dev libprotoc-dev zlib1g-dev bison flex make libftdi-dev  \
    libftdi1 libusb-1.0-0-dev liblo-dev libavahi-client-dev

    echo "END LINUX"
   ;;
  osx)
    echo "START OSX"
    brew install pkgconfig cppunit protobuf-cpp libmicrohttpd libusb py27-protobuf
    echo "END OSX"
  ;;
esac
echo "START install-deps"
git clone https://github.com/OpenLightingProject/ola.git ola
autoreconf -i
./configure --with-python
make
sudo make install
brew install python
brew link --overwrite python
sudo pip install pyinstaller
echo "END install-deps"
