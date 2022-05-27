ARG release=36
FROM fedora:${release}
# LABEL

# Install
RUN echo "Updating all base packages"; dnf -y update; dnf -y clean all
RUN echo "Installing fonts packages"; dnf -y install @fonts && dnf -y clean all
RUN echo "Installing fontconfig"; dnf -y install fontconfig && dnf -y clean all

COPY fontquery-container /fontquery

CMD ["/bin/bash"]
ENTRYPOINT ["/fontquery"]
