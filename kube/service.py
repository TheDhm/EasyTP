import kubernetes
from kubernetes import client, config
from pprint import pprint
from kubernetes.client.rest import ApiException


name = "gns3"
# service creation

config.load_kube_config()

api_instance = kubernetes.client.CoreV1Api()

#
# spec = client.V1ServiceSpec(selector={"app": name},
#                             type="NodePort",
#                             ports=[client.V1ServicePort(protocol="TCP", port=8080,
#                                                         node_port=40000,
#                                                         target_port=8080)])
#
# service = client.V1Service(api_version="V1",
#                            metadata=client.V1ObjectMeta(name=name + "-service"),
#                            spec=spec)


manifest = {
    "kind": "Service",
    "apiVersion": "v1",
    "metadata": {
        "name": "gns3-service"
    },
    "spec": {
        "selector": {
            "app": "gns3"
        },
        "ports": [
            {
                "protocol": "TCP",
                "port": 8080,
                "targetPort": 8080,
            }
        ],
        "type": "NodePort"
    }
}

try:
    api_response = api_instance.create_namespaced_service(namespace='default', body=manifest, pretty='true')
    pprint(api_response)
except ApiException as e:
    print("Exception when calling CoreV1Api->create_namespaced_endpoints: %s\n" % e)
