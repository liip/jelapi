from jelapi.classes import JelasticEnvironment, JelasticNodeGroup


def get_standard_node_group():
    return {"name": "cp"}


def get_standard_node_groups():
    ngs = []
    for ngtype in JelasticNodeGroup.NodeGroupType:
        ngs.append({"name": ngtype.value})
    return ngs


def get_standard_env(status=JelasticEnvironment.Status.RUNNING.value, extdomains=None):
    extdomains = extdomains if extdomains else []
    return {
        "shortdomain": "shortdomain",
        "domain": "domain",
        "envName": "envName",
        "displayName": "initial displayName",
        "status": status,
        "extdomains": extdomains,
        "nodeGroups": get_standard_node_groups(),
    }


def get_standard_node(fixed_cloudlets: int = 1, flexible_cloudlets: int = 1):
    return {
        "id": 1,
        "fixedCloudlets": fixed_cloudlets,
        "flexibleCloudlets": flexible_cloudlets,
        "intIP": "192.0.2.1",
        "nodeGroup": "cp",
        "url": "https://test.example.com",
        "diskIoLimit": 100000,
        "diskIopsLimit": 1000,
        "diskLimit": 20000,
        "endpoints": [],
        "features": ["FIREWALL"],
        "hasPackages": False,
        "isClusterSupport": False,
        "isCustomSslSupport": False,
        "isExternalIpRequired": False,
        "isHighAvailability": False,
        "isResetPassword": False,
        "isVcsSupport": False,
        "isWebAccess": True,
        "ismaster": True,
        "maxchanks": 32,
        "messages": [],
        "name": "image-name",
        "nodeGroup": "cp",
        "nodeType": "docker",
        "nodemission": "docker",
        "osType": "LINUX",
        "packages": [],
        "port": 22,
        "singleContext": False,
        "status": 1,
        "type": "NATIVE",
        "version": "docker-tag",
    }
