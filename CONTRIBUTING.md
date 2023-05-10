# Contributing to CasaOS AppStore

This document describes how to contribute an app to CasaOS AppStore.

## Guidelines

A CasaOS App is a Docker Compose app, or a *compose app*.

Each directory under [Apps](Apps) correspond to a CasaOS App. The directory should contain at least a `docker-compose.yml` file:

- It should be a valid [Docker Compose file](https://docs.docker.com/compose/compose-file/).

- The `name` property is used as the *store App ID*, which should be unique across all apps.

    For example, in the [`docker-compose.yml` of Syncthing](Apps/Syncthing/docker-compose.yml#L1), its store App ID is `syncthing`:

    ```yaml
    name: syncthing
    services:
        syncthing:
            image: linuxserver/syncthing:latest
    ...
    ```

- Language codes are case sensitive and should be in all lower case, e.g. `en_us`, `zh_cn`.

- CasaOS specific metadata, also called *store info*, are stored under [extension](https://docs.docker.com/compose/compose-file/#extension) property `x-casaos` at two positions.

    1. Service level

        A `docker-compose.yml` file can contain one or more `services`. Each [service](https://docs.docker.com/compose/compose-file/#services-top-level-element) can have its own store info.

        For the same example, at the buttom of the `syncthing` service in the [`docker-compose.yml` of Syncthing](Apps/Syncthing/docker-compose.yml)

        ```yaml
        x-casaos:
            envs:            # description of each environment variable
                ...
              - container: PUID
                description:
                    en_us: Run Syncthing as specified uid.
            ports:           # description of each port
              - container: "8384"
                description:
                    en_us: WebUI HTTP Port
                ...
            volumes:        # description of each volume
                - container: /config
                  description:
                      en_us: Syncthing config directory.
                - container: /DATA
                  description:
                    en_us: Syncthing Accessible Directory.
        ```

    1. Compose app level

        For the same example, at the bottom of the [`docker-compose.yml` of Syncthing](Apps/Syncthing/docker-compose.yml)

        ```yaml
        x-casaos:
            architectures:      # a list of architectures that the app supports
                - amd64
                - arm
                - arm64
            main: syncthing # the name of the main service under `services`
            author: CasaOS Team
            category: Backup
            description: # multiple locales are supported
                en_us: Syncthing is a continuous file synchronization program. It synchronizes files between two or more computers in real time, safely protected from prying eyes. Your data is your data alone and you deserve to choose where it is stored, whether it is shared with some third party, and how it's transmitted over the internet.
            developer: Syncthing
            icon: https://cdn.jsdelivr.net/gh/IceWhaleTech/CasaOS-AppStore@main/Apps/Syncthing/icon.png
            tagline:     # multiple locales are supported
                en_us: Free, secure, and distributed file synchronisation tool.
            thumbnail: https://cdn.jsdelivr.net/gh/IceWhaleTech/CasaOS-AppStore@main/Apps/Jellyfin/thumbnail.jpg
            title:       # multiple locales are supported
                en_us: Syncthing
            tips:
                before_install:
                    en_us: |
                        (some notes for user to read prior to installation, such as preset `username` and `password` - markdown is supported!)
            index: /         # the index page for web UI, e.g. index.html
            port_map: "8384" # the port for web UI
        ```
