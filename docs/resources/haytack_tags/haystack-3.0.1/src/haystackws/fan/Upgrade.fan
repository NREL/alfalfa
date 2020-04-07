//
// Copyright (c) 2015, Project-Haystack
// Licensed under the Academic Free License version 3.0
//
// History:
//   1 Oct 12  Brian Frank  Creation
//

using haystack
using sidewalk

**
** Upgrader
**
class Upgrade
{
  new make(Folio folio, Log log)
  {
    this.folio = folio
    this.log = log
  }

  const Folio folio
  const Log log

  Void run()
  {
  }

}