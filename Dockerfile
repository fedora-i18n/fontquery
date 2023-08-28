ARG release=38
FROM fedora:${release} AS base
# LABEL

# Install
COPY scripts/fontquery-setup.sh /usr/local/bin/fontquery-setup.sh
RUN echo "Setup base image"; /usr/local/bin/fontquery-setup.sh -t base

#
# minimal image
#
FROM base as minimal
ARG release
ENV RELEASE ${release}

# LABEL
LABEL description="Working environment for fontquery - minimal"
# Install
RUN echo "Installing default fonts packages"; fontquery-setup.sh -t minimal

CMD ["/usr/local/bin/fontquery-container", "--pattern", "minimal"]
ENTRYPOINT ["/usr/local/bin/fontquery-container", "--pattern", "minimal"]

#
# extra image
#
FROM minimal AS extra
ARG release
ENV RELEASE ${release}

# LABEL
LABEL description="Working environment for fontquery - extra"
# Install
RUN echo "Installing langpacks extra font packages"; fontquery-setup.sh -t extra

CMD ["/usr/local/bin/fontquery-container", "--pattern", "extra"]
ENTRYPOINT ["/usr/local/bin/fontquery-container", "--pattern", "extra"]

#
# all
#
FROM extra AS all
ARG release
ENV RELEASE ${release}

# LABEL
LABEL description="Working environment for fontquery - All fonts packages"
# Install
RUN echo "Installing all fonts packages"; fontquery-setup.sh -t all

CMD ["/usr/local/bin/fontquery-container", "--pattern", "all"]
ENTRYPOINT ["/usr/local/bin/fontquery-container", "--pattern", "all"]
