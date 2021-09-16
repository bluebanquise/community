#!/usr/bin/env python3

# ██████╗ ██╗     ██╗   ██╗███████╗██████╗  █████╗ ███╗   ██╗ ██████╗ ██╗   ██╗██╗███████╗███████╗
# ██╔══██╗██║     ██║   ██║██╔════╝██╔══██╗██╔══██╗████╗  ██║██╔═══██╗██║   ██║██║██╔════╝██╔════╝
# ██████╔╝██║     ██║   ██║█████╗  ██████╔╝███████║██╔██╗ ██║██║   ██║██║   ██║██║███████╗█████╗
# ██╔══██╗██║     ██║   ██║██╔══╝  ██╔══██╗██╔══██║██║╚██╗██║██║▄▄ ██║██║   ██║██║╚════██║██╔══╝
# ██████╔╝███████╗╚██████╔╝███████╗██████╔╝██║  ██║██║ ╚████║╚██████╔╝╚██████╔╝██║███████║███████╗
# ╚═════╝ ╚══════╝ ╚═════╝ ╚══════╝╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝ ╚══▀▀═╝  ╚═════╝ ╚═╝╚══════╝╚══════╝
#
# https://github.com/bluebanquise/
# Benoit Leveugle <benoit.leveugle@gmail.com>

from flask import Flask, request, jsonify
from celery import Celery
import time
import os
import sys
import subprocess
from subprocess import Popen, PIPE
import yaml
import logging
from ClusterShell.NodeSet import NodeSet
import ssh_wait
from datetime import datetime

# Colors, from https://stackoverflow.com/questions/287871/how-to-print-colored-text-in-terminal-in-python
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def load_file(filename):
    logging.info(bcolors.OKBLUE+'Loading '+filename+bcolors.ENDC)
    with open(filename, 'r') as f:
        #return yaml.load(f, Loader=yaml.FullLoader) ## Waiting for PyYaml 5.1
        return yaml.load(f)

app = Flask(__name__)
app.config['CELERY_BROKER_URL'] = 'pyamqp://root:root@localhost//'

celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)



##############################################################################
########### FLASK
##############################################################################

@app.route('/start_task', methods=['GET', 'POST', 'DELETE', 'PUT'])
def flask_start_task():
    task_data = request.get_json()
    print('Got new task with arguments:')
    print(task_data)
    print('Sending task to worker cluster queue...')
    counters = {'stage': 0, 'ssh_wait': 0}
    task = celery_execute_task.delay(task_data,tasks_list,counters)
    return jsonify({"Automate":"task submitted"})

##############################################################################
########### CELERY
##############################################################################

@celery.task
def celery_execute_task(task_data, tasks_list, counters):

    stage = counters['stage']

    # Internal processing
    ## Logs
    if 'node' in task_data:
        logs_path = '/var/log/bluebanquise/automate/' + task_data['node'] + '.log'
    else:
        logs_path = '/var/log/bluebanquise/automate/global.log'
    f = open(logs_path,'a')

    print('Entering new stage ' + str(stage) + ' for task ' + task_data['task'])
    f.write('Entering new stage ' + str(stage) + ' for task ' + task_data['task'] + '\n')
    f.write('Stage name: ' + tasks_list[task_data['task']][stage]['name'] + '\n')

    # Processing pre tasks
    ## Delay
    if 'delay_before' in tasks_list[task_data['task']][stage]:

        f.write('Waiting ' + str(tasks_list[task_data['task']][stage]['delay_before']) + 's' + '\n')
        time.sleep(tasks_list[task_data['task']][stage]['delay_before'])

    ## Ssh wait
    if 'wait_ssh_before' in tasks_list[task_data['task']][stage]:

        f.write('Checking ssh connectivity of host ' + task_data['node'] +'...\n')
        rc=ssh_wait.ssh_wait(task_data['node'],service='ssh',wait=True,wait_limit=tasks_list[task_data['task']][stage]['wait_ssh_before'],log_fn=print)
        if rc != 0:
            if 'wait_ssh_before_resubmit_on_fail' in tasks_list[task_data['task']][stage] and tasks_list[task_data['task']][stage]['wait_ssh_before_resubmit_on_fail'] and counters['ssh_wait'] < tasks_list[task_data['task']][stage]['wait_ssh_before_resubmit_on_fail_max_counter']:
                f.write('SSH timed out. Submitting again task to queue.' + '\n')
                counters['ssh_wait'] = counters['ssh_wait'] + 1
                task = celery_execute_task.delay(task_data, tasks_list, counters)
                f.close()
                return 0
            else:
                f.write('Failed to establish ssh connectivity to host.' + '\n')
                f.close()
                return 1
        else:
            f.write('Success to establish ssh connectivity.')

    # Processing task stage
    if 'commands' in tasks_list[task_data['task']][stage]:
        for cmd in tasks_list[task_data['task']][stage]['commands']:
            if 'exit_code' in cmd:
                exit_code = cmd['exit_code']
            else:
                exit_code = 0
            try:
                f.write('Executing command: ' + eval(cmd['command']) + '\n')
                child = subprocess.Popen( eval(cmd['command']), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
                stdout,stderr = child.communicate()
                if stdout is not None:
                    f.write(stdout.decode("utf-8"))
                if stderr is not None:
                    f.write(stderr.decode("utf-8"))
                rc = child.returncode
                f.write('Returned code: ' + str(rc) + '\n')
                if rc != 0:
                    print("Child was terminated by signal", rc, file=sys.stderr)
                    f.close()
                    return 1
                else:
                    print("Child returned", rc, file=sys.stderr)
            except OSError as e:
                print("Execution failed:", e, file=sys.stderr)
                f.close()
                return 1

        f.write('Task stage executed successfully.' + '\n')
        if (stage + 1) == len(tasks_list[task_data['task']]):
            print('Task ' + tasks_list[task_data['task']][stage]['name'] + ' done.')
            f.write('Task stage executed successfully.' + '\n')
        else:

            # Processing post tasks
            ## Delay
            if 'delay_after' in tasks_list[task_data['task']][stage]:
                f.write('Waiting ' + str(tasks_list[task_data['task']][stage]['delay_after']) + 's' + '\n')
                time.sleep(tasks_list[task_data['task']][stage]['delay_after'])
            ## Ssh wait
            if 'wait_ssh_after' in tasks_list[task_data['task']][stage]:
                f.write('Checking ssh connectivity of host ' + task_data['node'] + '\n')
                ssh_wait.ssh_wait(task_data['node'],service='ssh',wait=True,wait_limit=tasks_list[task_data['task']][stage]['wait_ssh_after'],log_fn=print)

            print('Now triggering next stage:')
            f.write('Now submitting next stage.' + '\n')
            counters['stage'] = counters['stage'] + 1
            task = celery_execute_task.delay(task_data, tasks_list, counters)
            f.close()
            return 0

##############################################################################
########### MAIN
##############################################################################

if __name__ == '__main__':
    # global g_user
    # global g_password
    global tasks_list
    # with open('/etc/worker_cluster/parameters.yml', 'r') as f:
    #     worker_cluster_parameters = yaml.load(f)
    with open('input.yml', 'r') as f:
        tasks_list = yaml.load(f)
    #g_user = worker_cluster_parameters['http_user']
    #g_password = worker_cluster_parameters['http_password']
    app.run()
