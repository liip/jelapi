from jelapi.classes import JelasticEnvironment


def get_standard_env(status=JelasticEnvironment.Status.RUNNING.value, extdomains=None):
    extdomains = extdomains if extdomains else []
    return {
        "shortdomain": "shortdomain",
        "domain": "domain",
        "envName": "envName",
        "displayName": "initial displayName",
        "status": status,
        "extdomains": extdomains,
    }


def get_standard_node():
    return {
        "id": 1,
        "fixedCloudlets": 1,
        "flexibleCloudlets": 1,
        "intIP": "192.0.2.1",
        "nodeGroup": "cp",
        "url": "https://test.example.com",
    }
