//
// Copyright (c) 2015, Project-Haystack
// Licensed under the Academic Free License version 3.0
//
// History:
//   22 Feb 11  Brian Frank  Creation
//

using concurrent
using wisp
using haystack
using util
using sidewalk
using sidewalkAdmin
using sidewalkEmail
using sidewalkForum
using sidewalkFileDoc
using sidewalkUser
using email

**
** Main for project-haystack web site
**
class Main : AbstractMain
{
  @Opt { help = "Print version information"; aliases = ["ver"] }
  Bool version

  @Opt { help = "HTTP port" }
  Int port := 8080

  Int printVersion(OutStream out, File distDir, File varDir)
  {
    out.printLine("Project-Haystack Web Site")
    out.printLine("Copyright (c) 2015, Project-Haystack")
    out.printLine("Licensed under the Academic Free License version 3.0")
    out.printLine("")
    out.printLine("java.version:     " + Env.cur.vars["java.version"])
    out.printLine("java.vm.name:     " + Env.cur.vars["java.vm.name"])
    out.printLine("java.vm.vendor:   " + Env.cur.vars["java.vm.vendor"])
    out.printLine("java.vm.version:  " + Env.cur.vars["java.vm.version"])
    out.printLine("java.home:        " + Env.cur.vars["java.home"])
    out.printLine("fan.version:      " + Pod.find("sys").version)
    out.printLine("fan.env:          " + Env.cur)
    out.printLine("fan.platform:     " + Env.cur.platform)
    out.printLine("haystack.version: " + Pod.of(this).version)
    out.printLine("isDev:            " + Sys.isDev)
    out.printLine("distDir:          " + distDir)
    out.printLine("varDir:           " + varDir)
    return 1
  }

  override Int run()
  {
    // app debug/production dirs
    homeDir := Sys.isDev ? Env.cur.workDir : Env.cur.workDir.parent
    distDir := homeDir + `dist/`
    varDir  := homeDir + `var/`
    if (!Folio.isInstalled)
    {
      homeDir = Env.cur.workDir
      distDir = homeDir
      varDir  = homeDir + `var/`
    }

    // check for version option
    if (version) return printVersion(Env.cur.out, distDir, varDir)

    // load tag database
    lib := HaystackLoader().load
    Lib.curRef.val = lib

    // email test
    Str? emailTestAddr := null
    if (Sys.isDev)
    {
      emailTestAddr = Env.cur.vars["SIDEWALK_EMAIL_TEST_ADDR"] ?: "no-one@nowhere.com"
      echo("##")
      echo("## Email disabled, test user: $emailTestAddr")
      echo("##")
    }

    // sidewalk modules
    mods := [
      "index":       HaystackIndexMod {},
      "doc":         HaystackDocMod {},
      "tag":         HaystackTagMod {},
      "download":    HaystackDownloadMod {},
      "about":       HaystackAboutMod {},
      "favicon.ico": FileMod { file = `fan://icons/x16/tag.png`.get },
      "pod":         PodMod {},
      "file":        FileDocMod { it.stdTags = ["magazine", "spec", "whitepaper", "logo", "misc"]; it.permissions = HaystackFileDocPermissions() },
      "forum":       ForumMod { it.renderer = HaystackForumRenderer# },
      "user":        UserMod {},
      "log":         LogMod {},
      "admin":       AdminMod {},
      "search":      HaystackSearchMod {},
    ]

    // handle if Folio database is installed
    if (Folio.isInstalled)
    {
      mods.addAll([
        "folio": FolioMod {},
        "email": EmailMod { it.testMode = emailTestAddr },
      ])
    }
    else
    {
      log.warn("Folio not installed")
    }

    // site URI for project
    siteDis := "Project Haystack"
    siteUri := Sys.isDev ?
               `http://localhost:$port/` :
               `http://project-haystack.org/`

    // boot up standard sidewalk system
    sys := Sys.makeApp(homeDir, "haystack", mods, HaystackTheme(), siteDis, siteUri, null)

    // launch wisp service
    WispService { it.httpPort = this.port ; it.root = SysMod(sys); }.start

    // run any upgrade routines
    if (Folio.isInstalled)
    {
      try
        Upgrade(sys.folio, log).run
      catch (Err e)
        log.err("Upgrade failed", e)
    }

    // loop forever
    log.info("Haystack launched ($sys.homeDir)")
    Actor.sleep(Duration.maxVal)
    return 0
  }
}

**************************************************************************
** HaystackFileDocPermissions
**************************************************************************

internal const class HaystackFileDocPermissions : FileDocPermissions
{
  override Bool canReadDoc(User? user, FileDoc doc) { true }
}