![Lint and Tests](https://github.com/liip/jelapi/workflows/Lint%20and%20Tests/badge.svg)
[![codecov](https://codecov.io/gh/liip/jelapi/branch/main/graph/badge.svg?token=ZjQDtiXWwO)](https://codecov.io/gh/liip/jelapi)

# jelapi

A Jelastic API Python library

## Installation

    pip3 install jelapi
    
## Usage

    from jelapi import JelasticAPI
    
    japi = JelasticAPI(apiurl='your.jelasticserver.test', apitoken='token')
     
    japi.redeployContainersByGroup(env, dockertag=dockertag, nodeGroup="cp")
