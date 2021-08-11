# High Availability

## Description

This role deploy and Active-Passive HA cluster based on PCS (corosync-pacemaker).

The role creates HA cluster on requested nodes, and then populate it with
desired resources and constraint.

This role can be combined with DBRD role to obtain shared storage across nodes.

## Instructions

Ensure your nodes are able to install HA components (may require a special
  subscription on RHEL OS).

### HA cluster

Create a group that contains only your HA cluster nodes, for example
`ha_cluster`, then in `inventory/group_vars/hacluster` folder, create a file
with the following variables, tuned to your needs:

```
high_availability_cluster_nodes:
  - name: ha1             # Hostname of the HA cluster nodes
    addrs:                # List of addresses to be used for HA ring (allow multiple rings for redundancy)
      - ha1
  - name: ha2
    addrs:
      - ha2
```

And deploy the HA cluster with these parameters.

Check cluster status after role deployment using:

```
pcs status
```

All nodes should be online.

If all goes well, it is then possible to add properties, resources,
constraints and stonith.

### Properties

Three kind of properties are supported currently by this role:

* pcs property
* psc resource op defaults
* pcs resource defaults

For each, it is possible to define a list of properties with their value:

```
high_availability_pcs_property:
  - name: cluster-recheck-interval
    value: 250
high_availability_pcs_resource_op_defaults:
  - name: action-timeout
    value: 40
high_availability_pcs_resource_defaults:
  - name: resource-stickiness
    value: 4300
  - name: migration-threshold
    value: 1
  - name: failure-timeout
    value: 40
```

### Resources

Resources are to be defined under variable `high_availability_resources`.
The role manage resources using groups, which acts as colocation constraint
(resources of the same group MUST be running on the same host at the same time),
and using definition order under that groups, which acts as a start order
constraint (if the first resource in the list fail to start, the second one
  will not start, etc).

For example:

```
high_availability_resources:
  - group: http
    resources:
      - id: vip-http
        type: IPaddr2
        arguments: "ip=10.10.0.7 cidr_netmask=255.255.0.0"
      - id: service-http
        type: systemd:httpd
  - group: dns
    resources:
      - id: vip-dns
        type: IPaddr2
        arguments: "ip=10.10.0.8 cidr_netmask=255.255.0.0"
      - id: service-dns
        type: systemd:named
```

In this example, resource `vip-http` and `service-http` belongs to the same
group `http`, and so will be running on the same host.
Also, since `vip-http` is listed before `service-http`, if `vip-http` fail to
start, then `service-http` will not start.

A list of resources for BlueBanquise CORE is provided at the end of this README.

### Constraint

Now that cluster is running resources, it is possible to add specific constraint
on groups (on top of groups and start order constraint already in place).

Two kind of constraints are available with this role: collocation and location.

#### Collocation constraint

Collocation allows to force a group to be close or not to another group.
The very common usage is to define collocation constraint that prevent some
group to be running on the same host than another.

For example, to set that `dns` group should never be running on the same host
than `http` group:

```
high_availability_resources:
  - group: http
    resources:
      - id: vip-http
        type: IPaddr2
        arguments: "ip=10.10.0.7 cidr_netmask=255.255.0.0"
      - id: service-http
        type: systemd:httpd
  - group: dns
    resources:
      - id: vip-dns
        type: IPaddr2
        arguments: "ip=10.10.0.8 cidr_netmask=255.255.0.0"
      - id: service-dns
        type: systemd:named
    colocations:
      - slave: http
        score: -INFINITY
```

#### Location constraint

Location allows to set a preferred node for a group of resources. This can be
useful to ensure a good load balancing between the ha cluster nodes.

For example, to set that `http` groups should be running on ha 2 node:

```
high_availability_resources:
  - group: http
    resources:
      - id: vip-http
        type: IPaddr2
        arguments: "ip=10.10.0.7 cidr_netmask=255.255.0.0"
      - id: service-http
        type: systemd:httpd
    locations:
      - type: prefers
        nodes:
          - ha2
```

### Stonith

Stonith (for "Shoot The Other Node In The Head") allows to prevent issues when a
node of the cluster is not working as expected or is unsynchronized with others.

It is possible to define stonith resources using this role. For example, to
define an IPMI stonith, use:

```
high_availability_stonith:
  - name: fenceha1
    type: fence_ipmilan                                                # IPMI fencing
    pcmk_host_check: static-list
    pcmk_host_list: ha1                                                # Target host to be stonith if issues
    pcmk_reboot_action: reboot                                         # Ask for reboot if fencing
    parameters: ipaddr=10.10.102.1 login=ADMIN passwd=ADMIN cipher=3   # Target host BMC ip and auth parameters for IPMI fencing
    prefers: ha2                                                       # Where this resource should be running
    avoids: ha1                                                        # Avoid resource to be running on own host
```

### List of standard resources

Bellow is a list of standard resources to be used with BlueBanquise. Note that
it can/must be adapted to needs (other kind of FS, multiple vip to handle multiple
  subnets, etc.).

#### Repositories and PXE

Since both repositories and PXE share the same service (http server), these must
be combined together in a same group.
Note that depending of tftp server used, service to set might be different.

Also, since bootset tool need to be usable from all nodes,
preboot_execution_environment folder should be in a separate volume, mounted and
exported through nfs, and mounted over nfs by all other HA cluster nodes.

So at the end, you need for this part 2 available FS shared between nodes, here
`/dev/repositories` and `/dev/pxe`, and a vip, here `10.10.77.1`.

```
- group: http
  resources:
    - id: fs-repositories
      type: Filesystem
      arguments: "device='/dev/repositories' directory='/var/www/html/repositories/' fstype='ext4'"
    - id: fs-pxe
      type: Filesystem
      arguments: "device='/dev/pxe' directory='/var/www/html/preboot_execution_environment/' fstype='ext4'"
    - id: vip-http
      type: IPaddr2
      arguments: "ip=10.10.77.1 cidr_netmask=255.255.0.0"
    - id: nfs-daemon-http
      type: nfsserver
      arguments: "nfs_shared_infodir=/var/www/html/preboot_execution_environment/nfsinfo nfs_no_notify=true"
    - id: nfs-export-pxe
      type: exportfs
      arguments: "clientspec=* options=rw,sync,no_root_squash directory=/var/www/html/preboot_execution_environment/ fsid=0"
    - id: service-http
      type: systemd:httpd
    - id: service-tftp
      type: systemd:atftpd

- group: pxe_mount
  resources:
    - id: nfs-mount-pxe
      type: Filesystem
      arguments: "device=10.10.77.1:/var/www/html/preboot_execution_environment/ directory=/var/www/html/preboot_execution_environment/ fstype=nfs clone interleave=true"
  colocations:
    - slave: http
      score: -INFINITY
```

So you should see something like this at the end for nfs-mount-pxe:

```
* Clone Set: nfs-mount-pxe-clone [nfs-mount-pxe]:
  * Started: [ ha2 ]
  * Stopped: [ ha1 ]
```

Where all nodes mount the nfs volume except one.

#### DHCP server

DHCP server do not need a virtual ip, expect for very specific cases.
Resource is simple to declare as only dhcp service is needed.

```
- group: dhcp
  resources:
    - id: service-dhcp
      type: systemd:dhcpd
```

#### DNS server

DNS server need a virtual ip, and the dns service.

```
- group: dns
  resources:
    - id: vip-dns
      type: IPaddr2
      arguments: "ip=10.10.77.2 cidr_netmask=255.255.0.0"
    - id: service-dns
      type: systemd:named
```

#### Time server

Time server is a bit tricky.
Chrony daemon is running on both clients and servers, and is using the same
configuration file path.

To solve this, execute time role 2 times, but with different configuration
path and client/server setting. Switch is then made using a simple
ocf_heartbeat_symlink resource and collocation constraint.

In the playbook, use:

```
roles:
  - role: time
    tags: time
    vars:
      time_profile: server
      time_chrony_custom_conf_path: /etc/chrony-server.conf
  - role: time
    tags: time
    vars:
      time_profile: client
      time_chrony_custom_conf_path: /etc/chrony-client.conf
tasks:
  - name: Remove base chrony configuration
    file:
      path: /etc/chrony.conf
      state: absent
```

This will generate both configurations, and ensure the default configuration is
not present. Then in HA resources, declare the following:

```
- group: time-server
  resources:
    - id: vip-time-server
      type: IPaddr2
      arguments: "ip=10.10.77.3 cidr_netmask=255.255.0.0"
    - id: time-server-symlink
      type: ocf:heartbeat:symlink
      arguments: "target=/etc/chrony-server.conf link=/etc/chrony.conf"
    - id: service-time-server
      type: systemd:chronyd

- group: time-client
  resources:
    - id: time-client-symlink
      type: ocf:heartbeat:symlink
      arguments: "target=/etc/chrony-client.conf link=/etc/chrony.conf clone interleave=true"
    - id: service-time-client
      type: systemd:chronyd
  colocations:
    - slave: time-server
      score: -INFINITY
```

#### Log server

Log server act as time server, you need to create 2 files, one for server and
one for client.

In the playbook, use:

```
roles:
  - role: log_server
    tags: log
    vars:
      log_server_rsyslog_custom_conf_path : /etc/rsyslog-server.conf
  - role: log_client
    tags: log
    vars:
      log_client_rsyslog_custom_conf_path : /etc/rsyslog-client.conf
tasks:
  - name: Remove base rsyslog configuration
    file:
      path: /etc/rsyslog.conf
      state: absent
```

This will generate both configurations, and ensure the default configuration is
not present. Then in HA resources, declare the following:

```
- group: log-server
  resources:
    - id: fs-log-server
      type: Filesystem
      arguments: "device='/dev/log-server' directory='/var/log/rsyslog/' fstype='ext4'"
    - id: vip-log-server
      type: IPaddr2
      arguments: "ip=10.10.77.4 cidr_netmask=255.255.0.0"
    - id: log-server-symlink
      type: ocf:heartbeat:symlink
      arguments: "target=/etc/rsyslog-server.conf link=/etc/rsyslog.conf"
    - id: service-log-server
      type: systemd:rsyslog

- group: log-client
  resources:
    - id: log-client-symlink
      type: ocf:heartbeat:symlink
      arguments: "target=/etc/rsyslog-client.conf link=/etc/rsyslog.conf"
    - id: service-log-client
      type: systemd:rsyslog
  colocations:
    - slave: log-server
      score: -INFINITY
```

## Changelog

* 1.0.0: Role creation. Benoit Leveugle <benoit.leveugle@gmail.com>
