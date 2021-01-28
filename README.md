[![Build Status](https://travis-ci.com/liip/jelapi.svg?branch=main)](https://travis-ci.com/liip/jelapi)
[![codecov](https://codecov.io/gh/liip/jelapi/branch/main/graph/badge.svg?token=ZjQDtiXWwO)](https://codecov.io/gh/liip/jelapi)

# jelapi

A Jelastic API Python library

## Installation

    pip3 install jelapi
    
## Usage

    from jelapi import JelasticAPI
    
    japi = JelasticAPI(apiurl='your.jelasticserver.test', apitoken='token')
     
    japi.redeployContainersByGroup(env, dockertag=dockertag, nodeGroup="cp")
