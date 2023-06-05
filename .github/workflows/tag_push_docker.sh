#!/bin/bash
SAVEIFS=$IFS
IFS=$'\n'
tags=($DOCKER_METADATA_OUTPUT_TAGS)
IFS=$SAVEIFS
for (( i=0; i<${#tags[@]}; i++))
do
    var=${tags[$i]}
    name=${var%:*}
    tag=${var#*:}
    docker tag $name:latest $var
    docker push $var
done
