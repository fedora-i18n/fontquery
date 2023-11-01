#! /bin/bash
# Copyright (C) 2023 Red Hat, Inc.
# SPDX-License-Identifier: MIT

. /etc/os-release

debug() {
  if [ -n "$DEBUG" ]; then
    echo "$*" >&2
  fi
}

msg_usage() {
  cat <<_E_
Image setup script

Usage: $PROG <options>
Options:
-h         Display this help and exit
-vose      Turn on debug
-t=TARGET  Set a TARGET build (base, minimal, extra, all)
_E_
}

PROG="${PROG:-${0##*/}}"
DEBUG="${DEBUG:-}"
OPT_TARGET="${OPT_TARGET:-minimal}"

while getopts hvt: OPT; do
  case "$OPT" in
    h)
      msg_usage
      exit 0
      ;;
    v)
      DEBUG=1
      shift
      ;;
    t)
      OPT_TARGET="$OPTARG"
      shift 2
      ;;
    *)
      msg_usage
      exit 1
      ;;
  esac
done

case "$ID" in
  fedora)
    case "$OPT_TARGET" in
      base)
        echo "Removing macros.image-language-conf if any"; rm -f /etc/rpm/macros.image-language-conf
        echo "Updating all base packages"; dnf -y update
        echo "Installing fontconfig"; dnf -y install fontconfig
        echo "Installing anaconda-core"; dnf -y install anaconda-core
        echo "Installing python packages"; dnf -y install python3-pip
        echo "Cleaning up dnf cache"; dnf -y clean all
        echo "Installing fontquery from PyPI"; pip install fontquery
        ;;
      minimal)
        if [ $VERSION_ID -ge 39 ]; then
        dnf -y install default-fonts
        else
        dnf -y --setopt=install_weak_deps=False install @fonts
        fi
        dnf -y clean all
        ;;
      extra)
        if [ $VERSION_ID -ge 39 ]; then
          dnf -y install langpacks-fonts-*
        else
          dnf -y install langpacks*
        fi
        dnf -y clean all
        ;;
      all)
        dnf -y --setopt=install_weak_deps=False install --skip-broken -x bicon-fonts -x root-fonts -x wine*-fonts -x php-tcpdf*-fonts -x texlive*-fonts -x mathgl-fonts -x python*-matplotlib-data-fonts *-fonts && dnf -y clean all
        ;;
      *)
        echo "Unknown target: $OPT_TARGET" >&2
        exit 1
        ;;
    esac
    ;;
  *)
    echo "Unsupported distribution: $ID" >&2
    exit 1
    ;;
esac
