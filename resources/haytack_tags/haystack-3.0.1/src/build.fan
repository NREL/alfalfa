#! /usr/bin/env fan
//
// Copyright (c) 2011, SkyFoundry LLC
// All Rights Reserved
//
// History:
//   16 Mar 11  Brian Frank  Creation
//

using build

**
** Web sites top level build script
**
class Build : BuildGroup
{

//////////////////////////////////////////////////////////////////////////
// Group
//////////////////////////////////////////////////////////////////////////

  new make()
  {
    childrenScripts =
    [
      `haystackws/build.fan`,
    ]
  }

//////////////////////////////////////////////////////////////////////////
// Overrides
//////////////////////////////////////////////////////////////////////////

  @Target { help = "Clean all, compile all, test all" }
  Void full()
  {
    runOnChildren("clean")
    runOnChildren("compile")
    runOnChildren("test")
  }

//////////////////////////////////////////////////////////////////////////
// Stage
//////////////////////////////////////////////////////////////////////////

  File? dist
  Str[]? reqPods

  @Target { help = "Stage the dist/ dir" }
  Void stage()
  {
    this.dist = scriptDir + `../dist/`
    this.reqPods = ["haystackws", "sidewalkFolio", "foliod", "icons"]

    log.info("stage [$dist]")
    log.indent

    buildDist
  }

  @Target { help = "Build zip distribution" }
  Void zip()
  {
    this.dist = scriptDir + `../zip/`
    this.reqPods = ["haystackws", "build", "compiler", "compilerJava", "icons"]
    ver := Pod.find("haystackws").version
    moniker := "haystack-$ver"
    file := scriptDir + `../${moniker}.zip`

    log.info("zip [$file]")
    log.indent

    // build dist to zip/ directory
    buildDist

    // copy src to zip/ directory
    scriptDir.copyInto(this.dist)

    // zip up distribution file
    zip := CreateZip(this)
    {
      outFile = file
      inDirs = [dist]
      pathPrefix = "$moniker/".toUri
      filter = |File f, Str path->Bool| { true }
    }
    zip.run
  }

  private Void buildDist()
  {

    // start fresh
    Delete(this, dist+`src/`).run
    Delete(this, dist+`bin/`).run
    Delete(this, dist+`etc/`).run
    Delete(this, dist+`lib/`).run

    // copy runtime files we need
    copyToDist(`bin/fan`)
    copyToDist(`bin/fanlaunch`)
    copyToDist(`etc/sys/`)
    copyToDist(`lib/java/sys.jar`)

    // figure out exactly what pods we need, and copy those
    pods := podsToDist()
    pods.each |pod|
    {
      file := Env.cur.findPodFile(pod.name)
      file.copyTo(dist+`lib/fan/${pod.name}.pod`)
    }

    log.unindent
  }

  Void copyToDist(Uri uri)
  {
    log.info("Copy [$uri]")
    devHomeDir.plus(uri).copyTo(dist.plus(uri))
  }

  Pod[] podsToDist()
  {
    // build up recursive list of haystack depends
    acc := Str:Pod[:]
    reqPods.each |req| { findPodDepends(acc, Pod.find(req)) }
    return acc.vals.sort
  }

  private Void findPodDepends(Str:Pod acc, Pod pod)
  {
    if (acc[pod.name] != null) return
    acc[pod.name] = pod
    pod.depends.each |d| { findPodDepends(acc, Pod.find(d.name)) }
  }

}