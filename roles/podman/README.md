# community/podman

Ansible role for setting up [podman](https://podman.io) in Bluebanquise environment.

This role is compatible with HA clusters:
* For active/active configuration please refer to the documentation since you need create 'bundles' to launch your containers: [How to create pacemaker container bundles using podman](https://access.redhat.com/solutions/3871591).
* For active/passive cluster

## Supported Platforms

* RedHat 8
* CentOS 8

## Requirements

Ansible 2.7 or higher is required for defaults/main/*.yml to work correctly.

## Variables

Variables for this role:

| variable | defaults/main/*.yml | type | description |
| -------- | ------------------- | ---- | ----------- |
| podman_configure | True | boolean | use default configuration when False, write config, when True |
| podman_configure_local_registry | False | boolean | starts a default local registry when True |
| podman_configure_ha | False | boolean | configure podman for a HA cluster |
| podman_users | { root: '100000:65535' } | dictionary | podman users that get uid mapping configured |
| podman_manual_mapping | True | boolean | ansible managed /etc/subuid and /etc/subgid entries |
| podman_search_registries | - 'docker.io' | items | list of registries that podman is pulling images from |
| podman_insecure_registries | [] | items | non TLS registries for podman, i.e. localhost:5000 |
| podman_blocked_registries | [] | items | blocked container registries |
| podman_local_registry_dir | "/var/lib/registry" | String | default local registry path when enabled |
| podman_local_registry_port | 5000 | integer | port of the local registry when enabled |
| podman_registry_container_path | /var/www/html/images/registry-2.tgz | String | path of the container used to spawn to default local registry when enabled |
| podman_conf_cgroup_manager | 'systemd' | string | /etc/container/libpod.conf: cgroup_manager |
| podman_conf_events_logger | 'file' | string | /etc/container/libpod.conf: events_logger, due to podman error with journald, see [issue](https://github.com/containers/libpod/issues/3126) |
| podman_conf_namespace | '' | string | /etc/container/libpod.conf: namespace (=default namespace) |
| podman_storage_driver | 'overlay' | string | storage driver |
| podman_storage_mountopt | 'nodev' | string | storage driver mount options |

## Dependencies

None.

## Example Playbook

For a basic setup with default values run:

```yaml
---
- hosts: management1
  vars:
    podman_configure_local_registry: True
    podman_users:
      root: '100000:65535'
      myuser1: '165536:65535'
      ...
    podman_registries:
      - 'registry.access.redhat.com'
      - 'docker.io'
      - 'localhost:5000'
  roles:
    - role: podman
```

## Local registry

In order to deploy the optionnal local registry, you must provide the container for it. This is done wih the following steps:

```shell
docker pull registry:2
docker save registry:2 | gzip > registry-2.tgz
scp registry-2 root@<management1>:/var/www/html/images/registry-2.tgz
```

## License and Author

* Author:: @strus38