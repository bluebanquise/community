# Prometheus

Note: this role comply with BlueBanquise data-model 1.0.0.

## Description

This role deploys Prometheus (server/client) with related ecosystem:

* Prometheus
* Alertmanager
* Karma
* ipmi_exporter
* snmp_exporter
* exporters:
   * slurm_exporter
   * node_exporter
   * ...
* Custom exporter python modules

The role provides a basic configuration that should match 80% of the cluster's
needs. An advanced configuration for specific usages is available and described
after the basic part.

## General instructions

You can refer to this diagram to help understanding of the following readme.

>>>>>>>>>> DIAGRAM HERE

### Server or/and client

**Server part** of the role deploy Prometheus, Alertmanager, Karma,
ipmi_exporter, snmp_exporter, and their respective configuration files and
service files.

To install server part, set `prometheus_server` to `true` at role invocation
vars. See server configure bellow for more details.

**Client part** of the role deploy other exporters or custom exporter
python modules on clients.

To install client part, set `prometheus_client` to `true` at role invocation
vars. See client configure bellow for more details.

**Important**: while server related variables are dedicated to server
configuration, client variables are used by **both** client and server part of
the role.

### Default ports

* Prometheus is available by default at http://localhost:9090
* Alertmanager is available by default at http://localhost:9093
* Karma is available by default at http://localhost:8080

## Basic Server configuration

><<<<<<<<<<<<<<< playbook



In the basic usage, the server role will install and setup the following tools:

* Prometheus: scrap and store metrics, fire alerts.
* Alertmanager: manage alerts fired by Prometheus.
* Karma: dashboard to monitor alerts managed by Alertmanager.
* ipmi_exporter: translate ipmi data to http scrapable by Prometheus.
* snmp_exporter: translate snmp data to http scrapable by Prometheus.

Which means all of these services will be running on the same management host.

>>>>>>>>>>>>>>>> Schema here

To manage what server part of the role should install and setup, defaults
variables can be used. The following variables, with their default values shown
here, are available:

```yaml
  prometheus_server_manage_alertmanager: true
  prometheus_server_manage_karma: true
  prometheus_server_manage_ipmi: false
  prometheus_server_manage_snmp: false
```

### Prometheus configuration

#### Scraping

By default, role will inherit from values set in its defaults folder.
You may wish to update these values to your needs, as these values set the
different timings used by Prometheus.

To do so, create file *inventory/group_vars/all/prometheus.yml* with the
following content (tuned to your needs):

```yaml
  prometheus_server_configuration:
    global_scrape_interval: 1m
    global_evaluation_interval: 2m
```

To understand the meaning of these values, refer to:

* https://prometheus.io/docs/prometheus/latest/configuration/configuration/#scrape_config
* https://www.robustperception.io/whats-the-difference-between-group_interval-group_wait-and-repeat_interval

**Warning**: size your storage available for Prometheus database according to
the size of the cluster and the scrape_interval set here.

These timings will apply to all exporters scraping. It is however possible to
tune specific timings for each exporter. This part is covered in the client
part of this readme.

#### Alerting

It is key to understand that in the Prometheus ecosystem, alerts are calculated
and fired **by Prometheus** and not Alertmanager. Alertmanager is a tool to
managed alerts that were fired by Prometheus (group alerts, send emails, etc).

By default, the role will only add a simple alerts file into the
/etc/prometheus/alerts folder. This file contains a basic alert that fire when
an exporter is down.

You will probably wish to add more alerts. You can add more files in this same
directory, and these will be loaded by Prometheus at startup.

To do so, either add them manually using another role (like >>>>>>>>>>>>>), or
add them in the inventory by adding in the file
*inventory/group_vars/all/prometheus_alerts.yml* the following content, tuned to
your needs:

```yaml
  prometheus_server_alerts:
    - >>>>>>>>>>>>>>>>>>>
```

### Alertmanager configuration

Alertmanager parameters can be updated by adding into the previously created
file *inventory/group_vars/all/prometheus.yml* the following content, tuned to
your needs:

```yaml
  prometheus_server_alertmanager_configuration:
    group_wait: 1m
    group_interval: 10m
    repeat_interval: 3h
```

To understand meaning of these values, refer to >>>>>>>>>>>>>>>>>

### Karma configuration

>>>>>>>>>>>

## Basic Client configuration

><<<<<<<<<<<<<<< playbook


The client side of the role install and start local exporters on nodes. It is
also used during server side of the role to know what to scrap on which group
of nodes.

Each exporter has its own http port. For example, Node_exporter is available at
http://localhost:9100 .

In order for this role to install and start exporters on the host, a
configuration is required in the Ansible inventory: a file is needed for each
**equipment_profile** group that should be monitored.
(See main documentation of BlueBanquise core to know what is an
equipment_profile.)

For example, to have equipment_typeL nodes installing and starting the
node_exporter exporter, you will need to create file
*inventory/group_vars/equipment_typeL/monitoring.yml* with the following content:

```yaml
  ep_monitoring:
    exporters:
      node_exporter:
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
setup to monitor much more things. This would be here, assuming managements
nodes are from equipment group equipment_typeM, a file
*inventory/group_vars/equipment_typeM/monitoring.yml* with the following content:

```yaml
  ep_monitoring:
    exporters:
      - name: node_exporter
        package: node_exporter
        service: node_exporter
        port: 9100
      - name: ha_cluster_exporter
        package: ha_cluster_exporter
        service: ha_cluster_exporter
        port: 9664
      - name: slurm_exporter
        package: slurm_exporter
        service: slurm_exporter
        scrape_interval: 5m
        scrape_timeout: 5m
        port: 9817
```

Note here that you can also set **scrape_interval** and **scrape_timeout**
values for each exporter here. These will override default values only for this
exporter.

Note that ha_cluster_exporter and slurm_exporter are documented in the stack,
but no packages are provided by the BlueBanquise project. Refer to the
monitoring main documentation to get additional details about these exporters.

## IPMI and SNMP

ipmi_exporter and snmp_exporter behave differently: they act as translation
gateways between Prometheus and the target. Which means, if you wish for example
to query IPMI data of a node, you do not install the exporter on the node itself.
This is why these two exporters are installed by the server part of the role and
not the client part.

To have the exporter installed by the server part of the role, set their
respective variables to true or false, according to your needs:

```yaml
  prometheus_server_manage_ipmi: true
  prometheus_server_manage_snmp: false
```

You then need to specify for each equipment_profile if you wish ipmi or/and snmp
to be scraped. To do so, set **scrap_ipmi** or/and **scrap_snmp** under
ep_monitoring to true. This can be combined (or not) with exporters.

```yaml
  ep_monitoring:
    exporters:
      - name: node_exporter
        package: node_exporter
        service: node_exporter
        port: 9100
    scrap_ipmi: true
    scrap_snmp: false
```

Since ipmi and snmp data are scraped using ipmi_exporter and snmp_exporter as
"translators", the server part of the Prometheus role will take these
variables into account to generate Prometheus, ipmi_exporter and snmp_exporter
configuration files.

Note: if variables are not set, role will consider them to false. This avoid
having to define them for each equipment_profile when not needed.




The role will then check each equipment_profile and if ipmi_exporter or/and
snmp_exporter exporters are defined under *monitoring.exporters*, then all nodes
of the equipment_profile will be added to the list of target to be scraped
through these exporters.

Example: User wish to gather IPMI data of all nodes of equipment_typeC. To do so,
create file *inventory/group_vars/equipment_typeC/monitoring.yml* with the
following content:

```yaml
  monitoring:
    exporters:
      ipmi_exporter:
        scrape_interval: 5m
        scrape_timeout: 5m
```

## To be done

* Global role reorganization
* Allow groups alerts selection.

## Changelog

* 1.0.1: Documentation. johnnykeats <johnny.keats@outlook.com>
* 1.0.0: Role creation. Benoit Leveugle <benoit.leveugle@gmail.com>, johnnykeats <johnny.keats@outlook.com>
