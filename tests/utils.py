from jelapi.classes import JelasticEnvironment, JelasticNodeGroup


def get_standard_node_group(
    node_group_type: JelasticNodeGroup.NodeGroupType = JelasticNodeGroup.NodeGroupType.APPLICATION_SERVER,
):
    return {"name": node_group_type.value}


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
        "hardwareNodeGroup": "a_provider_specific_string",
        "sslstate": True,
        "ishaenabled": False,
    }


def get_standard_node(
    id: int = 987, fixed_cloudlets: int = 1, flexible_cloudlets: int = 1
):
    return {
        "id": id,
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


def get_standard_mount_point(source_node_id: int = 1):
    return {
        "name": "mount point name",
        "path": "/tmp/test",
        "sourcePath": "/tmp/sourcePath",
        "sourceNodeId": source_node_id,
    }
