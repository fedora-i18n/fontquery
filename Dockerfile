ARG release=36
FROM fedora:${release} AS base
# LABEL

# Install
RUN echo "Removing macros.image-language-conf if any"; rm -f /etc/rpm/macros.image-language-conf
RUN echo "Updating all base packages"; dnf -y update
RUN echo "Installing fontconfig"; dnf -y install fontconfig
RUN echo "Installing anaconda-core"; dnf -y install anaconda-core
RUN echo "Cleaning up dnf cache"; dnf -y clean all

COPY fontquery-container /fontquery

CMD ["/bin/bash"]
ENTRYPOINT ["/fontquery"]

#
# comps image
#
FROM base AS comps
# LABEL
LABEL description="Working environment for fontquery - comps"
# Install
RUN echo "Installing fonts packages"; dnf -y install @fonts && dnf -y clean all

#
# langpacks image
#
FROM base AS langpacks
# LABEL
LABEL description="Working environment for fontquery - langpacks"
# Install
RUN echo "Installing langpacks packages"; dnf -y install langpacks* && dnf -y clean all

#
# both (comps + langpacks)
#
FROM comps AS both
# LABEL
LABEL description="Working environment for fontquery - comps + langpacks"
# Install
RUN echo "Installing langpacks packages"; dnf -y install langpacks* && dnf -y clean all

#
# all
#
FROM both AS all
# LABEL
LABEL description="Working environment for fontquery - All fonts packages"
# Install
RUN echo "Installing all fonts packages"; dnf -y install --skip-broken -x bicon-fonts -x root-fonts -x wine*-fonts -x php-tcpdf*-fonts -x texlive*-fonts -x mathgl-fonts -x python*-matplotlib-data-fonts *-fonts && dnf -y clean all
