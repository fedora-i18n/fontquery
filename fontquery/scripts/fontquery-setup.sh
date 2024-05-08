#! /bin/bash
# Copyright (C) 2023 Red Hat, Inc.
# SPDX-License-Identifier: MIT

set -e

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
-t=TARGET  Set a TARGET build (base, minimal, extra, all)
-c         Check for updates
-u         Update
-v         Turn on debug
_E_
}

PROG="${PROG:-${0##*/}}"
DEBUG="${DEBUG:-}"
OPT_TARGET="${OPT_TARGET:-minimal}"
OPT_UPDATE=0
OPT_CHECKUPDATE=0
DIST="${DIST:-}"

while getopts cht:uv OPT; do
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
        c)
            OPT_CHECKUPDATE=1
            ;;
        u)
            OPT_UPDATE=1
            ;;
        *)
            msg_usage
            exit 1
      ;;
  esac
done

if test "$OPT_CHECKUPDATE" -eq 1; then
    EXIT_STATUS=0
    case "$ID" in
        fedora|centos)
            echo "** Checking updates"
            dnf -y check-update
            EXIT_STATUS=$?
            ;;
        *)
            echo "Error: Unknown target: $OPT_TARGET" >&2
            exit 1
            ;;
    esac
    exit $EXIT_STATUS
fi

if test "$OPT_UPDATE" -eq 1; then
    EXIT_STATUS=0
    case "$ID" in
        fedora|centos)
            echo "** Updating packages"
            dnf -y update --setopt=protected_packages=,
            EXIT_STATUS=$?
            ;;
        *)
            echo "Error: Unknown target: $OPT_TARGET" >&2
            exit 1
            ;;
    esac
    exit $EXIT_STATUS
fi

case "$ID" in
    centos)
        DNFOPT=
        if [ $VERSION_ID -eq 10 ]; then
            # workaround for failing on mirror
            DNFOPT="--disablerepo=* --repofrompath=BaseOS,https://composes.stream.centos.org/stream-10/production/latest-CentOS-Stream/compose/BaseOS/x86_64/os --repofrompath=AppStream,https://composes.stream.centos.org/stream-10/production/latest-CentOS-Stream/compose/AppStream/x86_64/os --nogpgcheck"
        fi
        case "$OPT_TARGET" in
            base)
                echo "** Removing macros.image-language-conf if any"; rm -f /etc/rpm/macros.image-language-conf
                echo "** Updating all base packages"; dnf -y update $DNFOPT --setopt=protected_packages=,
                echo "** Installing fontconfig"; dnf -y $DNFOPT install fontconfig
                echo "** Installing anaconda-core"; dnf -y $DNFOPT install anaconda-core
                if [ $VERSION_ID -le 9 ]; then
                    echo "** Installing python packages"; dnf -y $DNFOPT install python3.11-pip
                else
                    echo "** Installing python packages"; dnf -y $DNFOPT install python3-pip
                fi
                echo "** Cleaning up dnf cache"; dnf -y $DNFOPT clean all
                PIP=""
                if [ -x "$(command -v pip)" ]; then
                    echo "** pip is available"
                    PIP="$(command -v pip)"
                elif [ -x "$(command -v pip3)" ]; then
                    echo "** pip3 is available"
                    PIP="$(command -v pip3)"
                elif [ -x "$(command -v pip3.11)" ]; then
                    echo "** pip3.11 is available"
                    PIP="$(command -v pip3.11)"
                fi
                if [ -z "$PIP" ]; then
                    echo "Error: pip not found" >& 2
                    exit 1
                fi
                if test -n "$DIST"; then
                    echo "** Installing fontquery from local"
                    echo $PIP install /tmp/$(basename $DIST)
                    $PIP install /tmp/$(basename $DIST)
                else
                    echo "** Installing fontquery from PyPI"
                    echo $PIP install "fontquery >= 1.10"
                    $PIP install "fontquery >= 1.10"
                fi
                rm /tmp/fontquery* || :
                ;;
            minimal)
                echo "** Installing minimal font packages"
                if [ $VERSION_ID -ge 10 ]; then
                    dnf -y $DNFOPT install default-fonts*
                else
                    dnf -y $DNFOPT --setopt=install_weak_deps=False install @fonts
                fi
                dnf -y $DNFOPT clean all
                ;;
            extra)
                echo "** Installing extra font packages"
                if [ $VERSION_ID -ge 10 ]; then
                    dnf -y $DNFOPT install langpacks-fonts-*
                else
                    dnf -y $DNFOPT install langpacks*
                fi
                dnf -y $DNFOPT clean all
                ;;
            all)
                echo "** Installing all font packages"
                dnf -y $DNFOPT --setopt=install_weak_deps=False install --skip-broken -x bicon-fonts -x root-fonts -x wine*-fonts -x php-tcpdf*-fonts -x texlive*-fonts -x mathgl-fonts -x python*-matplotlib-data-fonts *-fonts && dnf -y clean all
                ;;
            *)
                echo "Error: Unknown target: $OPT_TARGET" >&2
                exit 1
                ;;
        esac
        ;;
    fedora)
        case "$OPT_TARGET" in
            base)
                echo "** Removing macros.image-language-conf if any"; rm -f /etc/rpm/macros.image-language-conf
                echo "** Updating all base packages"; dnf -y update --setopt=protected_packages=,
                echo "** Installing fontconfig"; dnf -y install fontconfig
                echo "** Installing anaconda-core"; dnf -y install anaconda-core
                echo "** Installing python packages"; dnf -y install python3-pip
                echo "** Cleaning up dnf cache"; dnf -y clean all
                PIP=""
                if [ -x $(command -v pip) ]; then
                    echo "** pip is available"
                    PIP="$(command -v pip)"
                elif [ -x $(command -v pip3) ]; then
                    echo "** pip3 is available"
                    PIP="$(command -v pip3)"
                fi
                if [ -z "$PIP" ]; then
                    echo "Error: pip not found" >& 2
                    exit 1
                fi
                if test -n "$DIST"; then
                    echo "** Installing fontquery from local"
                    echo $PIP install /tmp/$(basename $DIST)
                    $PIP install /tmp/$(basename $DIST)
                else
                    echo "** Installing fontquery from PyPI"
                    echo $PIP install "fontquery >= 1.10"
                    $PIP install "fontquery >= 1.10"
                fi
                rm /tmp/fontquery* || :
                ;;
            minimal)
                echo "** Installing minimal font packages"
                if [ $VERSION_ID -ge 39 ]; then
                    dnf -y install default-fonts*
                else
                    dnf -y --setopt=install_weak_deps=False install @fonts
                fi
                dnf -y clean all
                ;;
            extra)
                echo "** Installing extra font packages"
                if [ $VERSION_ID -ge 39 ]; then
                    dnf -y install langpacks-fonts-*
                else
                    dnf -y install langpacks*
                fi
                dnf -y clean all
                ;;
            all)
                echo "** Installing all font packages"
                dnf -y --setopt=install_weak_deps=False install --skip-broken -x bicon-fonts -x root-fonts -x wine*-fonts -x php-tcpdf*-fonts -x texlive*-fonts -x mathgl-fonts -x python*-matplotlib-data-fonts *-fonts && dnf -y clean all
                ;;
            *)
                echo "Error: Unknown target: $OPT_TARGET" >&2
                exit 1
                ;;
        esac
         ;;
     *)
         echo "Error: Unsupported distribution: $ID" >&2
         exit 1
         ;;
esac
