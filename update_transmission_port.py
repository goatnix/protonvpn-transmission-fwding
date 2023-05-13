import yaml
import subprocess
import json

transmission_settings = "/home/user/transmission/config/settings.json"
docker_compose = "/home/user/transmission/docker-compose.yml"


def get_configured_port():
    with open(transmission_settings) as file:
        settings = json.load(file)
        configured_port = settings["peer-port"]
        return str(configured_port)


def get_current_port():
    subprocess.check_output(["natpmpc", "-a", "0", "0", "tcp", "60"])
    output = subprocess.check_output(["natpmpc", "-a", "0", "0", "udp", "60"])
    current_port = output.decode().split("Mapped public port ")[1].split()[0]
    return current_port


configured_port = get_configured_port()
current_port = get_current_port()

if configured_port != current_port:
    subprocess.run(["docker", "stop", "transmission"], check=True)
    with open(transmission_settings, "r+") as file:
        settings = json.load(file)
        settings["peer-port"] = int(current_port)
        file.seek(0)
        json.dump(settings, file, indent=4)
        file.truncate()

    with open(docker_compose, "r") as file:
        compose_data = yaml.safe_load(file)
        services = compose_data.get("services", {})
        for service in services.values():
            ports = service.get("ports", [])
            for i, port in enumerate(ports):
                ports[1] = f"{current_port}:{current_port}"
                ports[2] = f"{current_port}:{current_port}/udp"

    with open(docker_compose, "w") as file:
        yaml.dump(compose_data, file)

    subprocess.run(["docker-compose", "-f", docker_compose, "up", "-d"])
