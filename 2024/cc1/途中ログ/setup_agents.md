 $ ansible-playbook -i inventory.yaml setup_targets.yaml

PLAY [Deploy agents] ********************************************************************************************************************** 2024/12/08 12:44:58 (JST)

TASK [Gathering Facts] ******************************************************************************************************************** 2024/12/08 12:44:58 (JST)
ok: [webapp01]
ok: [db01]
ok: [nginx01]

TASK [agent : Ensure pprotein dir exists] ************************************************************************************************* 2024/12/08 12:45:03 (JST)
changed: [nginx01]
ok: [webapp01]
ok: [db01]

TASK [agent : Download pprotein] ********************************************************************************************************** 2024/12/08 12:45:05 (JST)
changed: [db01]
changed: [nginx01]
changed: [webapp01]

TASK [agent : Ensure node exporter dir exists] ******************************************************************************************** 2024/12/08 12:45:11 (JST)
ok: [webapp01]
changed: [nginx01]
ok: [db01]

TASK [agent : Download node exporter] ***************************************************************************************************** 2024/12/08 12:45:13 (JST)
changed: [db01]
changed: [nginx01]
changed: [webapp01]

TASK [agent : Ensure process exporter dir exists] ***************************************************************************************** 2024/12/08 12:45:19 (JST)
changed: [db01]
ok: [webapp01]
ok: [nginx01]

TASK [agent : Download Process Exporter] ************************************************************************************************** 2024/12/08 12:45:21 (JST)
changed: [nginx01]
changed: [db01]
changed: [webapp01]

TASK [agent : Create process exporter config file] **************************************************************************************** 2024/12/08 12:45:26 (JST)
ok: [nginx01]
changed: [webapp01]
ok: [db01]

TASK [agent : Create service unit files] ************************************************************************************************** 2024/12/08 12:45:30 (JST)
changed: [nginx01] => (item=etc/systemd/system/pprotein-agent.service)
ok: [webapp01] => (item=etc/systemd/system/pprotein-agent.service)
ok: [db01] => (item=etc/systemd/system/pprotein-agent.service)
changed: [nginx01] => (item=etc/systemd/system/node_exporter.service)
ok: [webapp01] => (item=etc/systemd/system/node_exporter.service)
ok: [db01] => (item=etc/systemd/system/node_exporter.service)
changed: [nginx01] => (item=etc/systemd/system/process-exporter.service)
ok: [db01] => (item=etc/systemd/system/process-exporter.service)
ok: [webapp01] => (item=etc/systemd/system/process-exporter.service)

TASK [agent : Start service] ************************************************************************************************************** 2024/12/08 12:45:43 (JST)
changed: [nginx01] => (item=pprotein-agent.service)
changed: [db01] => (item=pprotein-agent.service)
changed: [webapp01] => (item=pprotein-agent.service)
changed: [webapp01] => (item=node_exporter.service)
changed: [nginx01] => (item=node_exporter.service)
changed: [db01] => (item=node_exporter.service)
changed: [nginx01] => (item=process-exporter.service)
changed: [webapp01] => (item=process-exporter.service)
changed: [db01] => (item=process-exporter.service)

PLAY [Deploy db config] ******************************************************************************************************************* 2024/12/08 12:45:55 (JST)

TASK [Gathering Facts] ******************************************************************************************************************** 2024/12/08 12:45:55 (JST)
ok: [nginx01]
ok: [webapp01]
ok: [db01]

TASK [mysql : Deploy config] ************************************************************************************************************** 2024/12/08 12:45:58 (JST)
changed: [db01] => (item=etc/mysql/mysql.conf.d/mysqld.cnf)
changed: [webapp01] => (item=etc/mysql/mysql.conf.d/mysqld.cnf)
ok: [nginx01] => (item=etc/mysql/mysql.conf.d/mysqld.cnf)

RUNNING HANDLER [mysql : Restart mysql] *************************************************************************************************** 2024/12/08 12:46:03 (JST)
changed: [webapp01]
changed: [db01]

PLAY [Deploy nginx config] **************************************************************************************************************** 2024/12/08 12:46:10 (JST)

TASK [Gathering Facts] ******************************************************************************************************************** 2024/12/08 12:46:10 (JST)
ok: [webapp01]
ok: [nginx01]
ok: [db01]

TASK [nginx : Deploy config] ************************************************************************************************************** 2024/12/08 12:46:13 (JST)
changed: [webapp01] => (item=etc/nginx/nginx.conf)
ok: [nginx01] => (item=etc/nginx/nginx.conf)
ok: [db01] => (item=etc/nginx/nginx.conf)

RUNNING HANDLER [nginx : Restart nginx] *************************************************************************************************** 2024/12/08 12:46:17 (JST)
changed: [webapp01]

PLAY RECAP ******************************************************************************************************************************** 2024/12/08 12:46:19 (JST)
db01                       : ok=15   changed=7    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   
nginx01                    : ok=14   changed=7    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   
webapp01                   : ok=16   changed=9    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0  
