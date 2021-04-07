# Slurm

## Description

This role provides slurm configuration for controller (server), 
computes (client) and submitters (often called login) nodes.

## Instructions

**IMPORTANT**: before using the role, first thing to do is to generate a 
new munge key file. To do so, generate a new munge.key file using:

.. code-block:: text

  mungekey -c -k /etc/bluebanquise/roles/community/slurm/files/munge.key

I do not provide default munge key file, as it is considered a security risk.
(Too much users were using the example key).

Then, in the inventory addon folder (inventory/group_vars/all/addons that should
be created if not exist), add a slurm.yml file with the following content, tuned
according to your needs:

```yaml
  slurm_cluster_name: bluebanquise
  slurm_control_machine: management1
  slurm_computes_groups:
    - equipment_typeC
  slurm_partitions_list:
    - computes_groups:
        - equipment_typeC
      partition_name: typeC
      partition_configuration:
        State: UP
        MaxTime: "72:00:00"
        DefaultTime: "24:00:00"
        Default: yes
  slurm_all_partition:
      enable: true
      partition_configuration:
        State: UP
        MaxTime: "72:00:00"
        DefaultTime: "24:00:00"
```

To use this role for all 3 types of nodes, simply add a vars in the playbook
when loading the role. Extra vars is **slurm_profile**.

For a controller (server), use:

```yaml
  - role: slurm
    tags: slurm
    vars:
      slurm_profile: controller
```

For a compute node (client), use:

```yaml
  - role: slurm
    tags: slurm
    vars:
      slurm_profile: compute
```

And for a submitter (passive client, login), use:

```yaml
  - role: slurm
    tags: slurm
    vars:
      slurm_profile: submitter
```

### Accounting

If you enable accounting, once the role has been applyied on 
controller, check existence of the cluster in the database:

```
sacctmgr list cluster
```

If cluster is not here, add it using (assuming cluster name is *algoric*):

```
sacctmgr add cluster algoric
```

And check again if the cluster exist:

```
sacctmgr list cluster
```

## Input

Mandatory inventory vars:

**hostvars[inventory_hostname]**

* slurm_profile
* slurm
   * .cluster_name
   * .control_machine
   * .nodes_equipment_groups
   * .slurm_packaging

**hostvars[hosts]**

* ep_hardware
   * .cpu
      * .core

Optional inventory vars:

**hostvars[inventory_hostname]**

* slurm
   * .MpiDefault

## To be done

* slurmdbd + mariadb
* simple or static file (like nhc role)
* faster execution (include_tasks)

## Changelog

* 1.0.2: Update role, remove munge key. Benoit Leveugle <benoit.leveugle@gmail.com>
* 1.0.1: Documentation. Benoit Leveugle <benoit.leveugle@gmail.com>
* 1.0.0: Role creation. Benoit Leveugle <benoit.leveugle@gmail.com>
