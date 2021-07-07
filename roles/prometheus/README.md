# Prometheus

Note: this role comply with BlueBanquise data-model 1.0.0.

Table of content:

- [Prometheus](#prometheus)
  * [1. Description](#1-description)
  * [2. General instructions](#2-general-instructions)
    + [Server or/and client](#server-or-and-client)
    + [Default ports](#default-ports)
  * [3. Basic Server configuration](#3-basic-server-configuration)
    + [Prometheus configuration](#prometheus-configuration)
      - [Scraping](#scraping)
      - [Alerting](#alerting)
    + [Alertmanager configuration](#alertmanager-configuration)
    + [Karma configuration](#karma-configuration)
  * [4. Basic Client configuration](#4-basic-client-configuration)
  * [5. IPMI and SNMP](#5-ipmi-and-snmp)
  * [6. Advanced usage](#6-advanced-usage)
    + [Set custom launch parameters](#set-custom-launch-parameters)
    + [Manipulate firewall](#manipulate-firewall)
    + [Splitting services](#splitting-services)
    + [Adding raw prometheus.conf scraping jobs:](#adding-raw-prometheusconf-scraping-jobs-)
    + [Adding raw prometheus.conf configuration](#adding-raw-prometheusconf-configuration)
  * [Changelog](#changelog)

## 1. Description

This role deploys Prometheus (server/client) with related ecosystem:

* Prometheus (scrap metrics, store them, evaluate alerts)
* Alertmanager (manage alerts by grouping them, sending mails, etc)
* Karma (a dashboard for AlertManager)
* Am-executor
* ipmi_exporter
* snmp_exporter
* other exporters:
   * slurm_exporter
   * node_exporter
   * ...
* Custom exporter python modules

The role provides a basic configuration that should match 80% of the cluster's
needs. An advanced configuration for specific usages is available and described
after the basic part.

## 2. General instructions

You can refer to this diagram to help understanding of the following readme.

![File not found](resources/global_schema.svg "Main role schema")

### Server or/and client

**Server part** of the role deploys Prometheus, Alertmanager, Karma, Am-executor,
ipmi_exporter, snmp_exporter, and their respective configuration files and
service files.

To install server part, set `prometheus_server` to `true` at role invocation
vars. See server configuration bellow for more details.

**Client part** of the role deploys other exporters or custom exporter
python modules on clients.

To install client part, set `prometheus_client` to `true` at role invocation
vars. See client configuration bellow for more details.

**Important**: while server related variables are dedicated to server
configuration, client variables are used by **both** client and server part of
the role.

### Default ports

* Prometheus is available by default at http://localhost:9090
* Alertmanager is available by default at http://localhost:9093
* Karma is available by default at http://localhost:8080 (admin / admin)

## 3. Basic Server configuration

Playbook example:

```yaml
---
- name: Deploy prometheus server
  hosts: mg_managements
  roles:
    - role: prometheus
      vars:
        prometheus_server: true
```

In the basic usage, the server role will install and setup the following tools:

* Prometheus: scrap and store metrics, fire alerts.
* Alertmanager: manage alerts fired by Prometheus.
* Karma: dashboard to monitor alerts managed by Alertmanager.
* Am-executor: trigger actions in case of alert fired.
* ipmi_exporter: translate ipmi data to http scrapable by Prometheus.
* snmp_exporter: translate snmp data to http scrapable by Prometheus.

Which means all of these services will, by default, be running on the same
management host.

To manage what server part of the role should install and setup, defaults
variables can be used. The following variables, with their default values shown
here, are available:

```yaml
prometheus_server_manage_prometheus: true
prometheus_server_manage_alertmanager: true
prometheus_server_manage_karma: true
prometheus_server_manage_am_executor: false
prometheus_server_manage_ipmi_exporter: false
prometheus_server_manage_snmp_exporter: false
```

### Prometheus configuration

#### Scraping

By default, role will inherit from values set in its defaults folder.
You may wish to update these values to your needs, as these values set the
different timings used by Prometheus.

To do so, create file *inventory/group_vars/all/prometheus.yml* with the
following content (tuned to your needs, all global values can be defined):

```yaml
prometheus_server_configuration_global:
  scrape_interval: 1m
  scrape_timeout: 20s
  evaluation_interval: 2m
```

To understand the meaning of these values, refer to:

* https://prometheus.io/docs/prometheus/latest/configuration/configuration/#scrape_config
* https://www.robustperception.io/whats-the-difference-between-group_interval-group_wait-and-repeat_interval

If you do not set a value, Prometheus will use its defaults values, described
in the main documentation.

**Warning**: size your storage available for Prometheus database according to
the size of the cluster and the scrape_interval set here.

These timings will apply to all exporters scraping. It is however possible to
tune specific timings for each exporter. This part is covered in the client
section of this readme.

#### Alerting

It is key to understand that in the Prometheus ecosystem, alerts are calculated
and fired **by Prometheus** and not Alertmanager. Alertmanager is a tool to
managed alerts that were fired by Prometheus (group alerts, send emails, etc).

By default, the role will only add a simple alerts file into the
/etc/prometheus/alerts folder. This file contains very basic alerts related to
exporters down or Prometheus own scraping.

The role also offers to install few other alerts, each related to a specific exporter.
To install these additional alerts, simply enable them by adding them in the
**prometheus_server_additional_alerts** list variable. The following additional
alerts are available:

```yaml
prometheus_server_additional_alerts:
  - ipmi_exporter
  - node_exporter
```

You will probably wish to add more alerts. You can add more files in the
/etc/prometheus/alerts directory, and these will be loaded by Prometheus at
startup.

To do so, either add them manually using another role
(like [generic psf](https://github.com/bluebanquise/community/blob/main/roles/generic_psf)), or
add them in the inventory by adding their YAML code in the file
*inventory/group_vars/all/prometheus_alerts.yml*. For example:

```yaml
prometheus_server_custom_alerts:
  - alert: HostOutOfMemory
    expr: node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes * 100 < 10
    for: 2m
    labels:
      severity: warning
    annotations:
      summary: Host out of memory (instance {{ $labels.instance }})
      description: Node memory is filling up (< 10% left)\n  VALUE = {{ $value }}\n  LABELS: {{ $labels }}
  - alert: HostOutOfInodes
    expr: node_filesystem_files_free{mountpoint ="/rootfs"} / node_filesystem_files{mountpoint="/rootfs"} * 100 < 10 and ON (instance, device, mountpoint) node_filesystem_readonly{mountpoint="/rootfs"} == 0
    for: 2m
    labels:
      severity: warning
    annotations:
      summary: Host out of inodes (instance {{ $labels.instance }})
      description: Disk is almost running out of available inodes (< 10% left)\n  VALUE = {{ $value }}\n  LABELS: {{ $labels }}
```

### Alertmanager configuration

Alertmanager parameters are highly depending of users wishes.
Considering that, it is difficult to not propose a fully customizable parameters
file. This is why AlertManager whole configuration is contained in a single
variable, called **prometheus_server_alertmanager_raw_configuration**. The default
content is the following:

```yaml
prometheus_server_alertmanager_raw_configuration: |
  global:
    smtp_smarthost: 'localhost:25'
    smtp_from: 'alertmanager@your_domain'
    smtp_require_tls: false

  route:
    group_by: ['alertname', 'job']
    group_wait: 1m
    group_interval: 10m
    repeat_interval: 3h
    receiver: sys-admin-team

  receivers:
    - name: 'sys-admin-team'
      email_configs:
        - to: 'sys-admin-team@site.com'

  inhibit_rules:
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'cluster', 'service']
```

If you wish to tune the content of this file, simply copy this variable in the
inventory and tune it according to your needs.

To understand meaning of these values, refer to [main documentation](https://prometheus.io/docs/alerting/latest/configuration/)
or to [this page](https://www.robustperception.io/whats-the-difference-between-group_interval-group_wait-and-repeat_interval).

### Karma configuration

Few Karma parameters can be defined if needed.

To set kerma username and password, use:

```yaml
prometheus_server_karma_username: admin
prometheus_server_karma_password: admin
```

Default is admin / admin.

## 4. Basic Client configuration

Playbook example:

```yaml
---
- name: Deploy prometheus server
  hosts: mg_managements
  roles:
    - role: prometheus
      vars:
        prometheus_client: true
```

The client side of the role install and start local exporters on nodes.
Its inventory data are also used by server side of the role to know what to
scrap, on which group of nodes.

Each exporter has its own http port. For example, node_exporter is available at
http://localhost:9100 .

In order for this role to install and start exporters on the target host, a
configuration is required in the Ansible inventory: a file is needed for each
**equipment_profile** group that should be monitored.
(See main documentation of BlueBanquise CORE to know what is an
equipment_profile.)

For example, to have equipment_typeL nodes installing and starting the
node_exporter exporter, you will need to create file
*inventory/group_vars/equipment_typeL/monitoring.yml* with the following content:

```yaml
prometheus_client_exporters:
  - name: node_exporter
    package: node_exporter
    service: node_exporter
    port: 9100
```

For client part of the role, this means: all equipment_typeL nodes will install
node_exporter package and start node_exporter service.
For server part of the role, this means: all equipment_typeL nodes have to be
scraped on port 9100.
Again, client side variables are used by both client and server part of the role.

Another example: on your management nodes, you may wish to have more exporters
setup to monitor more things. This would be here, assuming managements
nodes are from equipment group equipment_typeM, a file
*inventory/group_vars/equipment_typeM/monitoring.yml* with the following content:

```yaml
prometheus_client_exporters:
  - name: node_exporter
    package: node_exporter
    service: node_exporter
    port: 9100
  - name: ha_cluster_exporter
    package: ha_cluster_exporter
    service: ha_cluster_exporter
    port: 9664
  - name: prometheus_slurm_exporter
    package: prometheus_slurm_exporter
    service: prometheus_slurm_exporter
    scrape_interval: 5m
    scrape_timeout: 5m
    port: 9101
```

Note here that you can also set **scrape_interval** and **scrape_timeout**
values for each exporter here. These will override default values only for this
exporter.

Note also that ha_cluster_exporter is documented in the stack,
but no packages are provided by the BlueBanquise project. Refer to the
monitoring main documentation to get additional details about this exporter.

## 5. IPMI and SNMP

ipmi_exporter and snmp_exporter behave differently: they act as translation
gateways between Prometheus and the target. Which means, if you wish for example
to query IPMI data of a node, you do not install the exporter on the node itself.
You query the ipmi_exporter, which will itself query the target for IPMI data.
This is why, in the basic configuration, these two exporters are installed by
the server part of the role and not the client part.

To have the exporter installed by the server part of the role, set their
respective variables to true or false, according to your needs:

```yaml
prometheus_server_manage_ipmi: true
prometheus_server_manage_snmp: false
```

You then need to specify for each equipment_profile if you wish ipmi or/and snmp
to be scraped. To do so, set the following values in the same monitoring.yml file
described in the client section of the role above.

```yaml
prometheus_ipmi_scrape: true
prometheus_ipmi_scrape_interval: 5m
prometheus_ipmi_scrape_timeout: 5m
prometheus_snmp_scrape: false
prometheus_snmp_scrape_interval:
prometheus_snmp_scrape_timeout:
```

Since ipmi and snmp data are scraped using ipmi_exporter and snmp_exporter as
"translators", the server part of the Prometheus role will take these
variables into account to generate Prometheus, ipmi_exporter and/or snmp_exporter
configuration files.

If variables are not set, role will consider them to false. This avoid
having to define them for each equipment_profile when not needed.

Note that you can set custom scrape_interval and scrape_timeout for ipmi or snmp
using dedicated variables shown in the example above.

Note also that ipmi_exporter will need `ep_equipment_authentication` dictionary
to be set for each equipment_profile that needs ipmi data scraping.

## 6. Advanced usage

### Set custom launch parameters

Since Prometheus ecosystem has been originally designed to run into containers,
some major parameters are passed to the binary at launch. This is why the current
role can update the systemd service file to integrate custom launch parameters.
Use variable **prometheus_server_launch_parameters** to achieve this.

For example, to manipulate data retention (default 15 days) and ask for 60 days,
set this variable:

```yaml
prometheus_server_launch_parameters:
  storage.tsdb.retention.time: 60d
```

Note that with recent version of Prometheus, you can also set the data base
maximum size instead. See more at https://www.robustperception.io/configuring-prometheus-storage-retention .

Another example, to manipulate database path, combine with a 60 days retention,
set:

```yaml
prometheus_server_launch_parameters:
  storage.tsdb.retention.time: 60d
  storage.tsdb.path: /prometheus
```

Etc. See all available options at https://gist.github.com/0x0I/eec137d55a26a16d836b84cbc186ab52 .

### Manipulate firewall

On some system, you may wish that the whole server side ecosystem is reachable
from the network or not (you may wish to reach it using an ssh port forwarding
only for example).

If variable `prometheus_firewall_open` is set to `true`, Prometheus and AlertManager will be reachable from the network on the `prometheus_server_firewall_zone` defined (default public). If not, firewall ports related to both will remain closed.

Example:

```yaml
prometheus_firewall_open: true
prometheus_server_firewall_zone: internal
```

Regarding client side, variable **prometheus_client_firewall_zone** allows to
set the firewall zone to be open for exporters to listen for queries.

### Splitting services

For some specific configurations, it is needed to split services over multiple
hosts.
For example to force ipmi_exporter and/or snmp_exporter to be deployed on
another host than the one running Prometheus.

To do so, disable ipmi and snmp on the hosts running Prometheus (host1), using this
configuration as host1 dedicated hostvars :

```yaml
prometheus_server_manage_prometheus: true
prometheus_server_manage_alertmanager: true
prometheus_server_manage_karma: true
prometheus_server_manage_am_executor: false
prometheus_server_manage_ipmi_exporter: false
prometheus_server_manage_snmp_exporter: false
```

And activate them on the host you wish them to run (host2), using the opposite values for host2 dedicated hostvars:

```yaml
prometheus_server_manage_prometheus: false
prometheus_server_manage_alertmanager: false
prometheus_server_manage_karma: false
prometheus_server_manage_am_executor: false
prometheus_server_manage_ipmi_exporter: true
prometheus_server_manage_snmp_exporter: true
```

To ensure everyone can communicate, set now these global variables in
group_vars/all (these variables are all set to localhost by default):

```yaml
prometheus_server_prometheus_host: host1
prometheus_server_alertmanager_host: host1
prometheus_server_karma_host: host1
prometheus_server_am_executor_host:
prometheus_server_ipmi_exporter_host: host2
prometheus_server_snmp_exporter_host: host2
```

This can be used to spread all main services.

Note: if any `prometheus_server_manage_X` variable is not defined, it is considered `false`.

Warning: if your firewall is running, you may need to open ports for desired
services.

### Adding raw prometheus.conf scraping jobs:

It is possible to inject raw scraping jobs into the
prometheus.conf file using the following multi lines variable:

```yaml
prometheus_server_prometheus_raw_jobs:
```

Note that you can combine this part and the [generic psf](https://github.com/bluebanquise/community/blob/main/roles/generic_psf)
role to create advanced configurations, like High Availability with Virtual IP.

### Adding raw prometheus.conf configuration

It is possible to inject raw prometheus configuration parameters into the
prometheus.conf file using the following multi lines variable:

```yaml
prometheus_server_prometheus_raw_configuration:
```

## Changelog

* 1.2.0: Role global enhancement. Benoit Leveugle <benoit.leveugle@gmail.com>
* 1.0.1: Documentation. johnnykeats <johnny.keats@outlook.com>
* 1.0.0: Role creation. Benoit Leveugle <benoit.leveugle@gmail.com>, johnnykeats <johnny.keats@outlook.com>
