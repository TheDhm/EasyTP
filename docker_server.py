import docker, re, time, datetime, requests
VERIFY_EVERY = 2
SHUTDOWN_INTERVAL_MINUTES = 20
client = docker.from_env()
# print(client.containers.list())
containers_activity = dict()
while True:
    for container in client.containers.list():
        command = container.exec_run(cmd="netstat -tan")[1]
        command = re.search("ESTABLISHED", str(command))
        if command:
            # print(command, container.name, "IS CONNECTED [*]")
            containers_activity[container.name] = datetime.datetime.now()

        else:
            print(container.name, "is inactive [*]")
            if not containers_activity.get(container.name, False):
                containers_activity[container.name] = datetime.datetime.now()
    containers_to_delete = []
    for elem in containers_activity:
        timediff = datetime.datetime.now() - containers_activity[elem]
        if timediff.seconds/60 >= SHUTDOWN_INTERVAL_MINUTES:
            print("Shutting down:", elem, "active since:", containers_activity[elem])
            client.containers.get(elem).stop()
            containers_to_delete.append(elem)
            try:
                r = requests.get("http://127.0.0.1:8000/refresh_instances/")
                if r.status_code == 200:
                    print("SERVER NOTIFIED [*]")
                else:
                    print("NO SERVER NOTIFICATION FOR THIS TIME[-]")
            except:
                print("NO SERVER NOTIFICATION FOR THIS TIME[-]")
    for i in containers_to_delete:
        del containers_activity[i]
    time.sleep(VERIFY_EVERY*60)
