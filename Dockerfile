ARG release=36
FROM fedora:${release} AS base
# LABEL

# Install
RUN echo "Removing macros.image-language-conf if any"; rm -f /etc/rpm/macros.image-language-conf
RUN echo "Updating all base packages"; dnf -y update
RUN echo "Installing fontconfig"; dnf -y install fontconfig
RUN echo "Installing anaconda-core"; dnf -y install anaconda-core
RUN echo "Installing python packages"; dnf -y install python3-pip
RUN echo "Cleaning up dnf cache"; dnf -y clean all
RUN echo "Installing fontquery from PyPI"; pip install fontquery


#
# comps image
#
FROM base AS comps
ARG release
ENV RELEASE ${release}

# LABEL
LABEL description="Working environment for fontquery - comps"
# Install
RUN echo "Installing fonts packages"; dnf -y install @fonts && dnf -y clean all

CMD ["/usr/local/bin/fontquery-container", "--pattern", "comps"]
ENTRYPOINT ["/usr/local/bin/fontquery-container", "--pattern", "comps"]

#
# langpacks image
#
FROM base AS langpacks
ARG release
ENV RELEASE ${release}

# LABEL
LABEL description="Working environment for fontquery - langpacks"
# Install
RUN echo "Installing langpacks packages"; dnf -y install langpacks* && dnf -y clean all

CMD ["/usr/local/bin/fontquery-container", "--pattern", "langpacks"]
ENTRYPOINT ["/usr/local/bin/fontquery-container", "--pattern", "langpacks"]

#
# both (comps + langpacks)
#
FROM comps AS both
ARG release
ENV RELEASE ${release}

# LABEL
LABEL description="Working environment for fontquery - comps + langpacks"
# Install
RUN echo "Installing langpacks packages"; dnf -y install langpacks* && dnf -y clean all

CMD ["/usr/local/bin/fontquery-container", "--pattern", "both"]
ENTRYPOINT ["/usr/local/bin/fontquery-container", "--pattern", "both"]

#
# all
#
FROM comps AS all
ARG release
ENV RELEASE ${release}

# LABEL
LABEL description="Working environment for fontquery - All fonts packages"
# Install
RUN echo "Installing all fonts packages"; dnf -y --setopt=install_weak_deps=False install --skip-broken -x bicon-fonts -x root-fonts -x wine*-fonts -x php-tcpdf*-fonts -x texlive*-fonts -x mathgl-fonts -x python*-matplotlib-data-fonts *-fonts && dnf -y clean all

CMD ["/usr/local/bin/fontquery-container", "--pattern", "all"]
ENTRYPOINT ["/usr/local/bin/fontquery-container", "--pattern", "all"]
