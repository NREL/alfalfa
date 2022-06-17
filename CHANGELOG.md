# Alfalfa Version 0.3.0

< fill out >

# Alfalfa Version 0.2.0

## Summary of updates

Worker:

- Install Spawn of EnergyPlus
- Alfalfa workers upgrade to PyFMI 2.9.5 and now use exclusively Python 3
- OS and FMU operations have improved separation
- Message to add a site now uses ‘model_name’ instead of ‘osm_name’ as a parameter
- FMU timestep updated to 60s.
- Timescale option now working for FMUs

Web:

- Resolved security vulnerabilities
- Windows compatible
- Isolated devDependencies
- Replaced deprecated Roboto dependency
- Localized Material Icons font
- ES6 refactor
- Reformat
- Added missing dependencies
- Replaced moment with luxon for tree shaking
- Replaced hardcoded browser targets with dynamic .browserslistrc
- Fixed invalid json
- Resolved all compilation warnings

Deployment:

- The [alfalfa-helm repo](https://github.com/NREL/alfalfa-helm) now provides resources for deploying Alfalfa to Kubernetes.

## What's Changed

- Print the error and traceback if worker dies during startup. by @anyaelena in https://github.com/NREL/alfalfa/pull/173
- lock version of poetry and force install nodejs by @nllong in https://github.com/NREL/alfalfa/pull/186
- Bump path-parse from 1.0.6 to 1.0.7 in /alfalfa_web by @dependabot in https://github.com/NREL/alfalfa/pull/184
- Bump browserslist from 4.13.0 to 4.16.6 in /alfalfa_web by @dependabot in https://github.com/NREL/alfalfa/pull/183
- Bump hosted-git-info from 2.8.8 to 2.8.9 in /alfalfa_web by @dependabot in https://github.com/NREL/alfalfa/pull/182
- Bump redis from 3.0.2 to 3.1.1 in /alfalfa_web by @dependabot in https://github.com/NREL/alfalfa/pull/180
- Bump ssri from 6.0.1 to 6.0.2 in /alfalfa_web by @dependabot in https://github.com/NREL/alfalfa/pull/179
- Bump y18n from 4.0.0 to 4.0.3 in /alfalfa_web by @dependabot in https://github.com/NREL/alfalfa/pull/187
- Bump lodash from 4.17.19 to 4.17.21 in /alfalfa_web by @dependabot in https://github.com/NREL/alfalfa/pull/181
- Update web dependencies by @kbenne in https://github.com/NREL/alfalfa/pull/190
- Bump aws-sdk from 2.715.0 to 2.814.0 in /alfalfa_web by @dependabot in https://github.com/NREL/alfalfa/pull/191
- Increase advance timeout to 1 minute by @kbenne in https://github.com/NREL/alfalfa/pull/193
- remove unused Dockerfile-test by @nllong in https://github.com/NREL/alfalfa/pull/215
- upgrade dependencies by @nllong in https://github.com/NREL/alfalfa/pull/214
- Support dev environment with docker-compose and docker by @nllong in https://github.com/NREL/alfalfa/pull/216
- rename docker-compose.historian.yml by @nllong in https://github.com/NREL/alfalfa/pull/217
- Break out files into worker fmu and worker openstudio folders by @nllong in https://github.com/NREL/alfalfa/pull/219
- move dbops.js out of generic lib folder by @nllong in https://github.com/NREL/alfalfa/pull/225
- Update copyrights and use prettier formatting pre-commit by @nllong in https://github.com/NREL/alfalfa/pull/226
- Remove .osm workflow from workers by @TShapinsky in https://github.com/NREL/alfalfa/pull/227
- rename osmName to modelName to support osm and fmu by @nllong in https://github.com/NREL/alfalfa/pull/223
- Update alfalfa-client branch by @nllong in https://github.com/NREL/alfalfa/pull/235
- Bump node-sass from 4.14.1 to 7.0.0 in /alfalfa_web by @dependabot in https://github.com/NREL/alfalfa/pull/232
- isort precommit by @nllong in https://github.com/NREL/alfalfa/pull/240
- Create dispatcher class by @nllong in https://github.com/NREL/alfalfa/pull/239
- Increase timeout for mlep to 1 min by @kbenne in https://github.com/NREL/alfalfa/pull/243
- Give E+ a minute to warm up. by @anyaelena in https://github.com/NREL/alfalfa/pull/246
- Remove redundant code in Alfalfa Workers by @TShapinsky in https://github.com/NREL/alfalfa/pull/244
- Update install commands for Spawn by @kbenne in https://github.com/NREL/alfalfa/pull/255
- Remove Python 2 by @TShapinsky in https://github.com/NREL/alfalfa/pull/251
- Web Refactor by @axelstudios in https://github.com/NREL/alfalfa/pull/267
- Bump ajv from 6.6.1 to 6.12.6 in /alfalfa_web by @dependabot in https://github.com/NREL/alfalfa/pull/269
- Main into develop by @anyaelena in https://github.com/NREL/alfalfa/pull/271
- Fixed datetime picker by @axelstudios in https://github.com/NREL/alfalfa/pull/277
- Add SuperLU with Sundials to fix spawn support by @TShapinsky in https://github.com/NREL/alfalfa/pull/278
- Bump paramiko from 2.9.2 to 2.10.1 by @dependabot in https://github.com/NREL/alfalfa/pull/281
- 263 fix fmutimescale by @anyaelena in https://github.com/NREL/alfalfa/pull/280

# Alfalfa Version 0.1.0

EnergyPlus Version: 9.4.0

OpenStudio Version: 3.1.0

Spawn Version: 0.0.1

JModelica from michaelwetter/ubuntu-1804_jmodelica_trunk
DIGEST:sha256:b7195e58a521636f2f56e1999fe6f0cdca64127fd3c2f575c6a0f6432b4778a9

Date Range 3/7/2017 - 3/10/2021
