#!/bin/bash
sleep 1.5
IP=$(ifconfig | grep -A1 eth0 | awk '/inet/ {print $2}')
ACT=$(awk '/host/ {print $3}' /data/.config/GNS3/2.2/gns3_server.conf)
awk -v ip="$IP" -v act="$ACT" '{ gsub(act, ip); print $0}' /data/.config/GNS3/2.2/gns3_server.conf > /tmp/out.conf
cat /tmp/out.conf > /data/.config/GNS3/2.2/gns3_server.conf
rm /tmp/out.conf