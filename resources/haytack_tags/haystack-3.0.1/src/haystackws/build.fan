#! /usr/bin/env fan
//
// Copyright (c) 2015, Project-Haystack
// All Rights Reserved
//
// History:
//   22 Feb 11  Brian Frank  Creation
//

using build

**
** Build: haystack
**
class Build : BuildPod
{
  new make()
  {
    podName = "haystackws"
    version = Version("3.0.1")
    summary = "Web site for project-haystack.org"
    depends = ["sys 1.0",
               "concurrent 1.0",
               "fandoc 1.0",
               "compilerDoc 1.0",
               "web 1.0",
               "webmod 1.0",
               "wisp 1.0",
               "email 1.0",
               "util 1.0",
               "haystack 2.1",
               "sidewalk 1.0",
               "sidewalkAdmin 1.0",
               "sidewalkEmail 1.0",
               "sidewalkFileDoc 1.0",
               "sidewalkForum 1.0",
               "sidewalkUser 1.0"]
    srcDirs = [`fan/`]
    resDirs = [`tags/`, `equips/`, `docs/`, `locale/`, `res/css/`, `res/img/`]
    docApi  = false
  }

}