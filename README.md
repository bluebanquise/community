## Community

![BlueBanquise Community](resources/pictures/BlueBanquise_Community_logo_large.png)

This repository hosts all community driven roles or tools around [**BlueBanquise**](https://github.com/bluebanquise/bluebanquise). These addition roles/tools can be new, or simply forks from the [core stack](https://github.com/bluebanquise/bluebanquise/tree/master/roles).

Each role/tool is owned by a developer, in charge of it.

Each owner can ask a new release of the repository, as this repository was made to provide fast releases cycle to core external roles/tools.

While the core stack aims to be multiple Linux distributions ready, each Community role owner is in charge of providing compatibility with Linux distributions (or not) for the additional role.

## List of available roles/tools

| Role/tool name        | Description                                              | Owner           | Link                                |
| --------------------- | -------------------------------------------------------- | --------------- | ----------------------------------- |
| clone                 | Clone to image and restore HDD                           | @johnnykeats    | [link](roles/clone/)                |
| display_tuning        | Provides screenrc configuration and iceberg shell colors | @oxedions       | [link](roles/display_tuning/)       |
| generic_psf           | Generic packages, services, folders and files            | @johnnykeats    | [link](roles/generic_psf/)          |
| grafana               | Install Grafana                                          | @oxedions       | [link](roles/grafana/)              |
| lmod                  | Install and configure Lmod                               | @oxedions       | [link](roles/lmod/)                 |
| nhc                   | Install and configure LBNL Node Health Check             | @oxedions       | [link](roles/nhc/)                  |
| ofed                  | Install OFED OpenFabrics                                 | @oxedions       | [link](roles/ofed/)                 |
| openldap              | Install and configure OpenLDAP and SSSD (beta)           | @oxedions       | [link](roles/openldap/)             |
| prometheus            | Install and configure Prometheus monitoring and alerting | @oxedions       | [link](roles/prometheus/)           |
| report                | Check inventory and gather helpful data                  | @oxedions       | [link](roles/report/)               |
| singularity           | Install and configure Singularity or SingularityPRO      | @strus38        | [link](roles/singularity/)          |
| slurm                 | Install and configure Slurm Workload Manager             | @oxedions       | [link](roles/slurm/)                |
| users_basic           | Set / remove users                                       | @oxedions       | [link](roles/users_basic/)          |

## List of external useful roles/tools

| Role/tool name        | Description                                              | Owner               | Link                                                    |
| --------------------- | -------------------------------------------------------- | ------------------- | ------------------------------------------------------- |
| System hardening      | Improve system security (os, apache, ssh, etc.)          | https://dev-sec.io/ | https://github.com/dev-sec/ansible-collection-hardening |
