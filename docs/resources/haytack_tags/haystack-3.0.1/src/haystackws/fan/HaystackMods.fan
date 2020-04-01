//
// Copyright (c) 2015, Project-Haystack
// Licensed under the Academic Free License version 3.0
//
// History:
//   22 Feb 11  Brian Frank  Creation
//   28 Mar 11  Brian Frank  Rework for new sidewalk framework
//

using web
using util
using sidewalk
using sidewalkFileDoc

//////////////////////////////////////////////////////////////////////////
// Index
//////////////////////////////////////////////////////////////////////////

const class HaystackIndexMod : SidewalkMod {}

const class HaystackIndexRoutes : Routes
{
  new make() : super([
    Route("",  GET,  #index, pubAccess),
  ]) {}

  Void index()
  {
    r := Renderer()
    r.writeStart("Home")
    r.out.print(Lib.cur.index)
    r.writeEnd
  }
}

//////////////////////////////////////////////////////////////////////////
// About
//////////////////////////////////////////////////////////////////////////

const class HaystackAboutMod : SidewalkMod {}

const class HaystackAboutRoutes : Routes
{
  new make() : super([
    Route("",  GET,  #index, pubAccess),
  ]) {}

  Void index()
  {
    r := Renderer()
    r.writeStart("About")
    r.out.print(Lib.cur.about)
    r.writeEnd
  }
}

//////////////////////////////////////////////////////////////////////////
// Tags
//////////////////////////////////////////////////////////////////////////

const class HaystackTagMod : SidewalkMod {}

const class HaystackTagRoutes : Routes
{
  new make() : super([
    Route("",     GET,  #index, pubAccess),
    Route("{0}",  GET,  #show,  pubAccess),
  ]) {}

  Void index()
  {
    r := Renderer()
    r.writeStart("Tags")
    r.out.print(Lib.cur.tags.index)
    r.writeEnd
  }

  Void show(Str tagName)
  {
    lib := Lib.cur
    tag := lib.tags.map[tagName]
    if (tag == null) { res.sendErr(404); return }

    r := Renderer()
    r.writeStart(tagName)
    r.out.print(tag.html)
    r.writeEnd
  }
}

//////////////////////////////////////////////////////////////////////////
// Docs
//////////////////////////////////////////////////////////////////////////

const class HaystackDocMod : SidewalkMod {}

const class HaystackDocRoutes : Routes
{
  new make() : super([
    Route("",     GET,  #index, pubAccess),
    Route("{0}",  GET,  #show,  pubAccess),
  ]) {}

  Void index()
  {
    r := Renderer()
    r.writeStart("Docs")
    r.out.print(Lib.cur.docs.index)
    r.writeEnd
  }

  Void show(Str fileName)
  {
    // process as doc chapter
    lib := Lib.cur
    doc := lib.docs.map[fileName]
    if (doc != null)
    {
      r := Renderer()
      r.writeStart(fileName)
      r.out.print(doc.html)
      r.writeEnd
      return
    }

    // lookup as resource file
    resource := typeof.pod.file(`/docs/${fileName}`, false)
    if (resource != null)
    {
      FileWeblet(resource).onGet
      return
    }

    res.sendErr(404)
  }
}

//////////////////////////////////////////////////////////////////////////
// Downloads
//////////////////////////////////////////////////////////////////////////

const class HaystackDownloadMod : SidewalkMod {}

const class HaystackDownloadRoutes : Routes
{
  new make() : super([
    Route("",                 GET,  #index,       pubAccess),
    Route("file/{0}",         GET,  #file,        pubAccess),
    Route("build/{0}",        GET,  #build,       pubAccess),
    Route("tags.txt",         GET,  #tagsText,    pubAccess),
    Route("tags.csv",         GET,  #tagsCsv,     pubAccess),
    Route("tz.txt",           GET,  #tzText,      pubAccess),
    Route("units.txt",        GET,  #unitsText,   pubAccess),
    Route("equip-points/{0}", GET,  #equipPoints, pubAccess),
    Route("locale/{0}",       GET,  #locale,      pubAccess),
  ]) {}

  Void index()
  {
    r := Renderer()
    r.writeStart("Downloads")

    r.out.h1.w("Downloads").h1End

    // FileDocs
    if (Folio.isInstalled)
    {
      allDocs := ((FileDocMod)sys.mod("file")).queryDocs(r.user)
      writeFilesSection(r, allDocs, "magazine",   "Haystack Connections Magazine")
      writeFilesSection(r, allDocs, "spec",       "Guide Specification")
      writeFilesSection(r, allDocs, "whitepaper", "Whitepaper")
      writeFilesSection(r, allDocs, "logo",       "Logos")
      writeFilesSection(r, allDocs, "misc",       "Misc File Downloads")
    }

    // static HTML
    r.out.print(Lib.cur.downloads)

    // Builds
    r.out.h2("id='builds'").w("Builds").h2End
    r.out.p.w("Source builds of this website:").pEnd
    r.out.ul
    try
    {
      files := sys.varDir.plus(`builds/`).listFiles.sortr |a, b| { toBuildVer(a) <=> toBuildVer(b) }
      files.each |f|
      {
        r.out.li.a(`/download/build/$f.name`).w(f.name).aEnd.liEnd
      }
    }
    catch (Err e) e.trace
    r.out.ulEnd

    r.writeEnd
  }

  private Void writeFilesSection(Renderer r, FileDoc[] allDocs, Str tag, Str dis)
  {
    docs := allDocs.findAll |d| { d.tags.has(tag) }
    if (docs.isEmpty) return

    out := r.out
    out.h2("id='$tag'").w(dis).h2End
    out.ul
    docs = docs.sort |a,b| { a.dis.localeCompare(b.dis) }
    docs.each |doc|
    {
      ext  := doc.fileExt
      size := doc.size.toLocale("B")
      out.li.a(`/file/$doc.id/$doc.fileName`, "class='$ext'").esc("${doc.dis}.$ext").aEnd.liEnd
    }
    out.ulEnd
  }

  private static Version toBuildVer(File f)
  {
    try
    {
      base := f.basename
      dash := base.index("-")
      return Version.fromStr(base[dash+1..-1])
    }
    catch (Err e) return Version.defVal
  }

  Void file(Str name)
  {
    // this has been replaced by FileDocMod, but kept around
    // so we don't break existing links (11-Jul-2016)
    if (name.contains("/") || name.contains("..")) { res.sendErr(404); return }
    f := sys.varDir + `files/$name`
    FileWeblet(f).onGet
  }

  Void build(Str name)
  {
    if (name.contains("/") || name.contains("..")) { res.sendErr(404); return }
    f := sys.varDir + `builds/$name`
    FileWeblet(f).onGet
  }

  Void tagsText()
  {
    // text/plain
    res.headers["Content-Type"] = "text/plain; charset=utf-8"
    out := res.out

    // write names
    lib := Lib.cur
    lib.tags.list.each |t| { out.printLine(t.name) }
  }

  Void tagsCsv()
  {
    // text/plain
    res.headers["Content-Type"] = "text/comma-separated-values; charset=utf-8"
    out := CsvOutStream(res.out)

    // write names
    lib := Lib.cur
    out.writeRow(["name", "kind"])
    lib.tags.list.each |t|
    {
      out.writeRow([t.name, t.kind])
    }
  }

  Void tzText()
  {
    // full names which begin with these regions are valid
    regions := Str:Str[:]
    ["Africa",
     "America",
     "Antarctica",
     "Asia",
     "Atlantic",
     "Australia",
     "Etc",
     "Europe",
     "Indian",
     "Pacific"].each |n| { regions[n] = n }

    // find valid names
    names := Str[,]
    TimeZone.listFullNames.each |n|
    {
      slash := n.index("/")
      if (slash == null) return
      if (regions[n[0..<slash]] == null) return
      name := n[n.indexr("/")+1..-1]
      names.add(name)
    }
    names.sort

    // text/plain
    res.headers["Content-Type"] = "text/plain; charset=utf-8"
    out := res.out

    // write names
    names.each |n| { out.printLine(n) }
  }

  Void unitsText()
  {
    // text/plain
    res.headers["Content-Type"] = "text/plain; charset=utf-8"
    out := res.out

    Unit.quantities.each |quantity|
    {
      out.printLine("-- $quantity --")
      Unit.quantity(quantity).each |unit|
      {
        out.printLine(unit.ids.join(","))
      }
      out.printLine
    }
  }

  Void equipPoints(Str name)
  {
    file := typeof.pod.file(`/equips/${name}.txt`, false)
    if (file == null) { res.sendErr(404); return }

    // text/plain
    res.headers["Content-Type"] = "text/plain; charset=utf-8"
    res.out.print(file.readAllStr)
  }

  Void locale(Str name)
  {
    file := typeof.pod.file(`/locale/${name}`, false)
    if (file == null) { res.sendErr(404); return }

    // text/plain
    res.headers["Content-Type"] = "text/plain; charset=utf-8"
    res.out.print(file.readAllStr)
  }
}

**************************************************************************
** Search
**************************************************************************

const class HaystackSearchMod : SidewalkMod {}

const class HaystackSearchRoutes : Routes
{
  new make() : super([
    Route("",  GET, #search, pubAccess),
  ]) {}

  Void search()
  {
    query := req.uri.query["q"] ?: ""
    uri := `http://google.com/#q=site:project-haystack.org+$query`
    res.redirect(uri)
  }
}

