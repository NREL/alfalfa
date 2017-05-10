//
// Copyright (c) 2015, Project-Haystack
// Licensed under the Academic Free License version 3.0
//
// History:
//   22 Feb 11  Brian Frank  Creation
//

using concurrent

**
** Lib stores all the static HTML content in immutable data structures.
**
const class Lib
{
  static Lib cur() { curRef.val }
  internal static const AtomicRef curRef := AtomicRef(null)

  new make(|This| f) { f(this) }

  const Str index
  const Str about
  const Str downloads
  const LibTags tags
  const LibDocs docs
}

** LibTags stores library of tags
const class LibTags
{
  new make(|This| f) { f(this) }

  const Str index
  const LibTag[] list
  const Str:LibTag map
}

** LibDoc stores library of docs
const class LibDocs
{
  new make(|This| f) { f(this) }

  const Str index
  const LibDoc[] list
  const Str:LibDoc map
}

** LibItem is base class for LibTag and LibDoc
const abstract class LibItem
{
  new make(|This| f) { f(this) }

  const Uri uri       // site absolute URI
  const Str name      // programatic name of doc/tag
  const Str summary   // summary HTML
  const Str html      // HTML page for item
}

** LibTag models static content of one tag
const class LibTag : LibItem
{
  new make(|This| f) : super(f) {}
  const Str kind      // kind string
}

** LibDoc models static content of one fandoc documentation page
const class LibDoc : LibItem
{
  new make(|This| f) : super(f) {}
}


