ARG release=36
FROM fedora:${release} AS base
# LABEL

# Install
RUN echo "Updating all base packages"; dnf -y update
RUN echo "Installing fontconfig"; dnf -y install fontconfig && dnf -y clean all

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
RUN echo "Installing all fonts packages"; dnf -y install --skip-broken *-fonts && dnf -y clean all
