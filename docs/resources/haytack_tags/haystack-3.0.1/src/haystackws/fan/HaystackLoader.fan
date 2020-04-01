//
// Copyright (c) 2015, Project-Haystack
// Licensed under the Academic Free License version 3.0
//
// History:
//   22 Feb 11  Brian Frank  Creation
//

using fandoc
using haystack
using web
using compilerDoc::DocFandoc
using compilerDoc::DocLoc

class HaystackLoader
{

//////////////////////////////////////////////////////////////////////////
// Load
//////////////////////////////////////////////////////////////////////////

  Lib load()
  {
    echo("Haystack Database loading...")
    stubTags
    stubDocs
    loadDocIndex
    mapPrevNext
    genTags
    genDocs
    echo("Haystack Database loaded [$tags.size tags, $docs.size docs]")
    return toLib
  }

//////////////////////////////////////////////////////////////////////////
// Tags
//////////////////////////////////////////////////////////////////////////

  private Void stubTags()
  {
    // iterate each tags/{foo}.trio file
    typeof.pod.files.each |f|
    {
      // look for /doc/{name}.fandoc
      if (!f.pathStr.startsWith("/tags/") || f.ext != "trio") return

      // parse trio file into recs
      in := TrioReader(f.in)
      in.eachRec |rec|
      {
        try
          stubTag(rec)
        catch (Err e)
          err("${f.name}:${in->lineNum}: Invalid tag '${rec->tag}' - $e")
      }
    }

    // flatten and sort
    tags = tagsMap.vals.sort |a, b| { a.name <=> b.name }
  }

  ** Map dict read from trio into XTag
  private Void stubTag(Dict rec)
  {
    x := XTag(rec->tag, rec)
    if (tagsMap[x.name] != null) err("Duplicate tag definitions: $x.name")

    // do an initial parse of fandoc
    doc := (Str)rec->doc
    x.fandocStr = doc
    x.fandoc = parseFandoc(x.name, x.fandocStr.in)

    // check kind
    x.kind = rec->kind
    if (kinds[x.kind] == null) throw Err("Invalid kind: $x.kind")

    // get first sentence as summary fandoc
    summary := DocFandoc(DocLoc.unknown, doc).firstSentence.text
    x.summaryFandoc = parseFandoc(x.name, summary.in)

    // recursively map all the anchors in document
    mapAnchorIds(x, x.fandoc)

    // store it
    tagsMap[x.name] = x
  }

  private Void genTags()
  {
    tags.each |tag| { genTag(tag) }
  }

  private Void genTag(XTag x)
  {
    // map references
    x.alsoSee  = tagRefs(x, "alsoSee")
    x.usedWith = tagRefs(x, "usedWith")

    // generate summary fandoc to html
    x.summaryHtml = writeFandoc(x, x.summaryFandoc)

    // generate details page
    x.html = TagDetailsRenderer(this, x).render
  }

  private XTag[] tagRefs(XTag x, Str key)
  {
    if (x.dict.missing(key)) return XTag#.emptyList
    acc := XTag[,]
    x.dict[key].toStr.split(',').each |name|
    {
      t := tagsMap[name]
      if (t == null) err("Invalid ref ${x.name}.$key: $name")
      else acc.add(t)
    }
    return acc
  }

//////////////////////////////////////////////////////////////////////////
// Docs
//////////////////////////////////////////////////////////////////////////

  private Void stubDocs()
  {
    typeof.pod.files.each |f|
    {
      // look for /doc/{name}.fandoc
      if (!f.pathStr.startsWith("/docs/") || f.ext != "fandoc") return

      // stub fandoc into doc
      stubDoc(f)
    }
  }

  ** Map fandoc file into TagDoc
  private Void stubDoc(File f)
  {
    // create and map stub
    x := XDoc(f.basename)

    // do an initial parse of fandoc
    x.fandocStr = f.readAllStr
    x.fandoc = parseFandoc(x.name, x.fandocStr.in)

    // recursively map all the anchors in document
    mapAnchorIds(x, x.fandoc)

    // store it
    docsMap[x.name] = x
  }

  private Void loadDocIndex()
  {
    // parse from index.fog
    docIndex = typeof.pod.file(`/docs/index.fog`).readObj

    // check that index and actual docs match up
    check := docsMap.dup
    ordered := XDoc[,]
    docIndex.findAll |x| {x is List} .each|Obj[] item|
    {
      name := item[0].toStr
      doc := check.remove(name)
      if (doc == null) err("Doc index maps to unknown doc: $name")
      else
      {
        doc.summary = item[1]
        ordered.add(doc)
      }
    }
    check.each |doc| { err("Doc not in index: $doc.name") }

    // store sorted flattened list
    this.docs = ordered
  }

  private Void genDocs()
  {
    docs.each |tag| { genDoc(tag) }
  }

  private Void genDoc(XDoc x)
  {
    x.html = DocRenderer(this, x).render
  }

//////////////////////////////////////////////////////////////////////////
// Fandoc
//////////////////////////////////////////////////////////////////////////

  Doc parseFandoc(Str name, InStream in)
  {
    doc := FandocParser().parse(name, in)
    walkLinks(doc)
    return doc
  }

  private Void walkLinks(DocElem elem)
  {
    newChildren := DocNode[,]
    elem.children.each |child, i|
    {
      if (child is Link)
      {
        explodeLink(child).each |link| { newChildren.add(link) }
      }
      else
      {
        if (child.id !== DocNodeId.text) walkLinks(child)
        newChildren.add(child)
      }
    }
    elem.removeAll.addAll(newChildren)
  }

  private DocNode[] explodeLink(Link orig)
  {
    if (orig.uri.startsWith("equip:")) return explodeEquipPoints(orig)
    return [orig]
  }

  private DocNode[] explodeEquipPoints(Link orig)
  {
    name := orig.uri["equip:".size..-1]
    file := typeof.pod.file(`/equips/${name}.txt`)
    acc := DocNode[,]
    file.eachLine |line|
    {
      // skip empty lines or comment lines
      line = line.trim
      if (line.isEmpty || line.startsWith("//")) return

      // heading lines
      if (line.startsWith("**"))
      {
        doc := FandocParser().parse(name, line.in)
        acc.addAll(doc.children)
        doc.removeAll
        return
      }

      // parse line of tag names into list item of links
      item := ListItem()
      line.split.each |tag, i|
      {
        if (i > 0) item.add(DocText(" "))
        link := Link(tag)
        link.isCode = true
        link.add(DocText(tag))
        item.add(link)
      }

      // add to current bullet list
      ul := acc.last as UnorderedList
      if (ul == null) acc.add(ul = UnorderedList())
      ul.add(item)
    }
    return acc
  }

//////////////////////////////////////////////////////////////////////////
// To Lib
//////////////////////////////////////////////////////////////////////////

  private Lib toLib()
  {
    return Lib
    {
      it.index     = IndexRenderer().render
      it.about     = AboutRenderer().render
      it.downloads = DownloadsRenderer().render
      it.tags      = toLibTags
      it.docs      = toLibDocs
    }
  }

  private LibTags toLibTags()
  {
    index := TagIndexRenderer(this).render
    list  := LibTag[,]
    map   := Str:LibTag[:]
    tags.each |x| { t := toLibTag(x); list.add(t); map[t.name] = t }
    return LibTags { it.index = index; it.list = list; it.map = map }
  }

  private LibDocs toLibDocs()
  {
    index := DocIndexRenderer(this).render
    list  := LibDoc[,]
    map   := Str:LibDoc[:]
    docs.each |x| { t := toLibDoc(x); list.add(t); map[t.name] = t }
    return LibDocs { it.index = index; it.list = list; it.map = map }
  }

  private LibTag toLibTag(XTag x)
  {
    LibTag { uri = `/tag/${x.name}`; name = x.name; kind = x.kind; html = x.html; summary = x.summaryHtml }
  }

  private LibDoc toLibDoc(XDoc x)
  {
    LibDoc { uri = `/doc/${x.name}`; name = x.name; html = x.html; summary = x.summary }
  }

//////////////////////////////////////////////////////////////////////////
// Utils
//////////////////////////////////////////////////////////////////////////

  private Void mapPrevNext()
  {
    tags.each |tag, i|
    {
      tag.prev = (i > 0) ? tags[i-1] : null
      tag.next = tags.getSafe(i+1)
    }

    docs.each |doc, i|
    {
      doc.prev = (i > 0) ? docs[i-1] : null
      doc.next = docs.getSafe(i+1)
    }
  }

  private Void mapAnchorIds(XItem x, DocElem elem)
  {
    id := elem.anchorId
    if (id != null)
    {
      if (x.anchorIds[id] != null)
        err("Doc $x.name has duplicate anchor id $id")
      else
        x.anchorIds[id] = id
    }
    elem.children.each |child| { if (child is DocElem) mapAnchorIds(x, child) }
  }

  internal Str writeFandoc(XItem x, DocElem elem)
  {
    buf := StrBuf()
    out := LoaderFandocWriter(this, x, buf.out)
    elem.children.each |child| { child.write(out) }
    return buf.toStr
  }

  Void err(Str msg, Err? err := null)
  {
    echo("ERROR: $msg")
    if (err != null) err.trace
  }

//////////////////////////////////////////////////////////////////////////
// Fields
//////////////////////////////////////////////////////////////////////////

  static const Str:Bool kinds := [
    "Marker":true,
    "Bool":true,
    "Number":true,
    "Str":true,
    "Uri":true,
    "Ref":true,
    "Bin":true,
    "Date":true,
    "Time":true,
    "DateTime":true,
    "Obj":true,
    "Coord":true]

  internal Obj[]? docIndex
  internal XTag[]? tags
  internal XDoc[]? docs
  internal Str:XTag tagsMap := [:]
  internal Str:XDoc docsMap := [:]
}

internal class XItem
{
  new make(Str n, Uri u) { this.name = n; this.uri = u }
  override Str toStr() { name }
  const Str name
  const Uri uri
  Str:Str anchorIds := [:]
  Str? html
  Doc? fandoc
  Str? fandocStr
  XItem? prev
  XItem? next
}

internal class XTag : XItem
{
  new make(Str n, Dict dict) : super(n, `/tag/${n}`) { this.dict = dict }
  const Dict dict
  Doc? summaryFandoc
  Str? summaryHtml
  Str? kind
  XTag[]? alsoSee
  XTag[]? usedWith
}

internal class XDoc : XItem
{
  new make(Str n) : super(n, `/doc/${n}`) {}
  Str? summary
}

internal class LoaderFandocWriter : HtmlDocWriter
{
  new make(HaystackLoader loader, XItem curItem, OutStream out) : super(out)
  {
    this.curItem = curItem
    this.loader  = loader
  }

  XItem curItem
  HaystackLoader loader

  override Void elemStart(DocElem elem)
  {
    if (elem.id === DocNodeId.link)
    {
      link := elem as Link
      try
      {
        link.uri = mapUri(link.uri)
        link.isCode = link.uri.startsWith("/tag/")
      }
      catch (Err e) loader.err("Cannot map $link.uri", e)
    }
    super.elemStart(elem)
  }

  Str mapUri(Str uri)
  {
    // check if absolute
    if (uri.startsWith("http://")) return uri
    if (uri.startsWith("https://")) return uri

    // split "{path}#{frag}"
    Str path := uri
    Str? frag := null
    pound := uri.index("#")
    if (pound != null) { path = uri[0..<pound]; frag = uri[pound+1..-1] }

    // check for special fixed URIs or URIs already mapped
    if (path.startsWith("/"))
    {
      if (path == "/download") return uri
      if (path.startsWith("/tag/")) return uri
      if (path.startsWith("/doc/")) return uri
      loader.err("$curItem: Invalid abs uri '$uri'")
      return uri
    }

    // check for internal fragments
    if (path.isEmpty)
    {
      if (curItem.anchorIds[frag] == null)
        loader.err("$curItem: Invalid internal fragment '$uri'")
      return curItem.uri.toStr + "#" + frag
    }

    // Docs vs tag
    isDoc := path[0].isUpper
    item := isDoc ? loader.docsMap[path] : loader.tagsMap[path]

    // check base link
    if (item == null)
    {
      loader.err("$curItem: Invalid link name '$uri'")
    }
    else
    {
      if (frag != null && item.anchorIds[frag] == null)
        loader.err("$curItem: Invalid link fragment '$uri'")
    }

    base := isDoc ? "/doc/" : "/tag/"
    return base + uri
  }

}