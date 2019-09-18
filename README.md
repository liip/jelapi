# jelapi

A Jelastic API Python library

## Installation

    pip3 install jelapi
    
## Usage

    from jelapi import JelasticAPI
    
    japi = JelasticAPI(apiurl='your.jelasticserver.test', apitoken='token')
     
    japi.redeployContainersByGroup(env, dockertag=dockertag, nodeGroup="cp")
