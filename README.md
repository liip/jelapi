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
    for _, env in jelenvs.items()
    if all(eg in env.envGroups for eg in ["clients/envgroup", "prod"])
)

for n in jelenv.nodes:
    n.fixedCloudlets = 2

cpnode = jelenv.node_by_node_group("cp")
cpnode.fixedCloudlets = 2
cpnode.envVars["AN_ENV_VARIABLE"] = "Content"

sqlnode = jelenv.nodeGroups["sqldb"].nodes[0]
sqlnode.flexibleCloudlets = max(sqlnode.flexibleCloudlets - 2, 0)
sqlnode.allowFlexibleCloudletsReduction = True

jelenv.save()
```
