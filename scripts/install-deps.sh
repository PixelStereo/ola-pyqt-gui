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
    brew install pkgconfig cppunit libmicrohttpd libusb
    brew install protobuf
    export PATH="$PATH:/usr/local/bin/"
    export PKG_CONFIG_PATH="/opt/local/lib/pkgconfig:$PKG_CONFIG_PATH"
    export CPPFLAGS="-I/opt/local/include"
    export LDFLAGS="-L/opt/local/lib"
    export PYTHONPATH=/usr/local/lib/python2.7/site-packages/:/opt/local/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/site-packages
    echo "END OSX"
  ;;
esac

echo ""
echo ""
echo "------------------"
echo "START install-deps"
echo "------------------"
echo "$TRAVIS_OS_NAME"
echo "------------------"
echo ""
echo ""
echo ""
echo ""
echo ""
echo ""
echo ""
echo ""
echo ""
brew install python
brew link --overwrite python
git clone https://github.com/OpenLightingProject/ola.git ola
cd ola
autoreconf -i
./configure --enable-python-libs
make
sudo make install
cd ../
sudo pip install pyinstaller
echo ""
echo ""
echo ""
echo ""
echo ""
echo ""
echo ""
echo ""
echo ""
echo '-----------------'
echo "END install-deps"
echo "------------------"
echo ""
echo ""