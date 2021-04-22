![Lint and Tests](https://github.com/liip/jelapi/workflows/Lint%20and%20Tests/badge.svg)
[![codecov](https://codecov.io/gh/liip/jelapi/branch/main/graph/badge.svg?token=ZjQDtiXWwO)](https://codecov.io/gh/liip/jelapi)

# jelapi

A Jelastic API Python library

## Installation

    pip3 install jelapi
    
## Usage

```
import jelapi

jelapi.api_url = "https://app.jpc.infomaniak.com/1.0/"
jelapi.api_token = "your-long-token"

jelenvs = jelapi.JelasticEnvironment.list()

jelenv = next(
    env
    for env in jelenvs.values()
    if all(eg in env.envGroups for eg in ["clients/envgroup", "prod"])
)

for ng in jelenv.nodeGroups.values():
    for n in ng.nodes:
        n.fixedCloudlets = 2

cpnodegroup = jelenv.nodeGroups("cp"]
cpnodegroup.nodes[0].fixedCloudlets = 2
cpnodegroup.envVars["AN_ENV_VARIABLE"] = "Content"

sqlnode = jelenv.nodeGroups["sqldb"].nodes[0]
sqlnode.flexibleCloudlets = max(sqlnode.flexibleCloudlets - 2, 0)
sqlnode.allowFlexibleCloudletsReduction = True

jelenv.save()
```
