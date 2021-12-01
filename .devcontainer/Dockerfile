FROM debian:11-slim
ARG DEB_MIRROR=http://ftp.de.debian.org/debian

# non-root user settings
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID

# Create non-root user
RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
    #
    # [Optional] Add sudo support. Omit if you don't need to install software after connecting.
    && apt-get update \
    && apt-get install -y sudo \
    && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME

# Install additional packages.
ENV DEBIAN_FRONTEND=noninteractive
RUN echo "deb ${DEB_MIRROR} bullseye main" > /etc/apt/sources.list \
    && apt-get update --allow-releaseinfo-change \
    && apt-get -y install --no-install-recommends \
        build-essential \
        python3 \
        python3-pip \
        python3-dev \
        python3-stdeb \
        python3-all \
        debhelper \
        dh-python \
        git \
        bash-completion \
        locales \
        procps \
        #
        # Shells
        zsh \
        fish \
        #
        # cli tools
        jq \
        # Enable git ssh and gpg inside container
        ssh \
        gnupg2 \
    #
    # Cleanup apt cache
    && rm -f /var/cache/apt/archives/*.deb /var/cache/apt/archives/partial/*.deb /var/cache/apt/*.bin || true

RUN locale-gen en_US.UTF-8 # Fix locale errors
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

# Global pip config (workaround due to errors downloading pip packages when working in corporate environments)
COPY .devcontainer/pip.conf /root/.config/pip/pip.conf
COPY .devcontainer/pip.conf /home/$USERNAME/.config/pip/pip.conf

# Install requirements (using pip)
COPY requirements.txt requirements-dev.txt /tmp/
RUN pip3 install -r /tmp/requirements.txt -r /tmp/requirements-dev.txt

# Load custom profiles
# Configure bash settings
WORKDIR "/home/${USERNAME}"
RUN echo "Preparing shells" \
    #
    # bash
    && echo 'if ls /workspaces/*/.devcontainer/profile.sh >/dev/null 2>&1; then source /workspaces/*/.devcontainer/profile.sh; fi' >> ".bashrc" \
    #
    # zsh
    && echo 'if ls /workspaces/*/.devcontainer/profile.sh >/dev/null 2>&1; then source /workspaces/*/.devcontainer/profile.sh; fi' >> ".zshrc" \
    #
    # fix permissions
    && chown -R ${USERNAME}:${USERNAME} . \
    #
    # Change default shell
    && usermod -s /usr/bin/zsh $USERNAME

# Set default user
USER $USERNAME
