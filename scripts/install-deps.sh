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
    echo "END LINUX"
   ;;
  osx)
    echo "START OSX"
    echo "nothing to do… brew is already installed on osx"
    echo "END OSX"
  ;;
esac
echo "START install-deps"
brew install python
brew link --overwrite python
sudo pip install pyinstaller
#sudo pip3 install pyinstaller
echo "END install-deps"
