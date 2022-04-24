#!/bin/bash
IP=$(ip route show | awk '/172.17.0.0/ {print $9}')
awk -v ip="$IP" '{ gsub("localhost", ip); print $0}' /data/.config/GNS3/2.2/gns3_server.conf > out.conf
cat out.conf > /data/.config/GNS3/2.2/gns3_server.conf
rm out.conf