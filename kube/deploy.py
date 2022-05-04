import kubernetes
from kubernetes import client, config

config.load_kube_config()

# deployment creation
apps_api = client.AppsV1Api()

name = "gns3"
image = "gns3:latest"

container = client.V1Container(name=name,
                               image=image,
                               ports=[client.V1ContainerPort(container_port=8080)],
                               image_pull_policy="Never",
                               env=[client.V1EnvVar(name="VNC_PW",
                                                    value="0000")]
                               )
spec = client.V1DeploymentSpec(selector=client.V1LabelSelector(match_labels={"app": name}),
                               replicas=1,
                               template=client.V1PodTemplateSpec(metadata=client.V1ObjectMeta(labels={"app": name}),
                                                                 spec=client.V1PodSpec(containers=[container]))
                               )

deployment = client.V1Deployment(api_version="apps/v1",
                                 kind="Deployment",
                                 metadata=client.V1ObjectMeta(name=name + "-deployment"),
                                 spec=spec
                                 )

apps_api.create_namespaced_deployment(namespace="default", body=deployment)
