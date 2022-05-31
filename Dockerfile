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

RUN echo "Installing fonts packages"; dnf -y install @fonts && dnf -y clean all

#
# langpacks image
#
FROM base AS langpacks

# Install
RUN echo "Installing langpacks packages"; dnf -y install langpacks* && dnf -y clean all
