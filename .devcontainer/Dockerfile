FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    wget \
    ca-certificates \
    apt-transport-https \
    gnupg \
    lsb-release \
    software-properties-common

RUN apt-get update && apt-get install -y \
    sudo

RUN apt-get update && apt-get install -y --no-install-recommends \
    texlive-bibtex-extra \
    texlive-extra-utils \
    texlive-fonts-recommended \
    texlive-fonts-extra \
    texlive-lang-english \
    texlive-lang-italian \
    texlive-latex-base \
    texlive-latex-extra \
    texlive-latex-recommended \
    texlive-luatex \
    texlive-pictures \
    texlive-science \
    texlive-xetex \
    ghostscript

RUN apt-get update && apt-get install -y --no-install-recommends \
    latexmk \
    libfile-homedir-perl \
    libunicode-linebreak-perl \
    libyaml-perl \
    libyaml-tiny-perl \
    perl \
    perl-doc

RUN apt-get update && apt-get install -y --no-install-recommends \
    biber

# Clean up the image
RUN apt-get clean && rm -rf /var/lib/apt/lists/*

RUN useradd -m -s /bin/bash vscode && \
    echo 'vscode ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

WORKDIR /workspace

USER vscode

ENV SHELL=/bin/bash
