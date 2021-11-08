
Install needed repositories via rpms:

dnf install -y epel-release
dnf install -y centos-release-rabbitmq-38



variables
worker_cluster_rabbitmq_reference_node



```yaml
deploy_diskless:
  - name: Deploy playbook on diskless node
    commands:
      - command: '"ansible-playbook /etc/bluebanquise/playbooks/" + task_data["playbook"] + " -t identify --limit " + task_data["node"]'
    wait_ssh_before: 40

deploy_node:
  - name: Set node to boot next time on osdeploy
    commands:
      - command: '"bootset -b osdeploy -n " + task_data["node"]'
  - name: Reboot node and wait 10s after
    commands:
      - command: '"powerman --cycle " + task_data["node"]'
      - command: '"echo 7 >> /var/www/html/preboot_configuration_environment/nodes/" + task_data["node"] + ".stage"'
    delay_after: 10
  - name: Deploy playbook on node once OS has been deployed
    commands:
      - command: '"echo 10 >> /var/www/html/preboot_configuration_environment/nodes/" + task_data["node"] + ".stage"'
      - command: '"ansible-playbook /etc/bluebanquise/playbooks/" + task_data["playbook"] + " --limit " + task_data["node"]'
      - command: '"echo 0 >> /var/www/html/preboot_configuration_environment/nodes/" + task_data["node"] + ".stage"'
    wait_ssh_before: 20
    wait_ssh_before_resubmit_on_fail: true
    wait_ssh_before_resubmit_on_fail_max_counter: 30
```
