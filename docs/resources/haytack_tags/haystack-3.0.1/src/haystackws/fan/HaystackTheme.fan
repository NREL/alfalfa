//
// Copyright (c) 2015, Project-Haystack
// Licensed under the Academic Free License version 3.0
//
// History:
//   22 Feb 11  Brian Frank  Creation
//   28 Mar 11  Brian Frank  Rework for new sidewalk framework
//

using fandoc
using web
using sidewalk

internal const class HaystackTheme : Theme
{
  override Void writeStart(Renderer r, Str titleStr)
  {
    siteDis := r.sys.siteDis
    user    := r.req.user
    userMod := r.sys.userMod

    // head
    r.res.headers["Content-Type"] = "text/html; charset=utf-8"
    out := r.out
    out.docType
    out.html
    out.head
      .title.w("$titleStr.toXml &ndash; $siteDis.toXml").titleEnd
      .w("<meta name='Description' content='Project Haystack is an open source initiative to
          develop naming conventions and taxonomies for building equipment and operational data' />").nl
      .includeCss(`http://fonts.googleapis.com/css?family=Droid Sans:regular,bold`)
      .includeCss(`http://fonts.googleapis.com/css?family=Droid Serif:regular,italic,bold`)
      r.writeHeadIncludes
      out.includeCss(`/pod/haystackws/res/css/site.css`)
         .includeCss(`/pod/haystackws/res/css/sidewalk.css`)
      .w("<!--[if lt IE 8]>").nl
      .includeCss(`/pod/haystackws/res/css/ie7.css`)
      .w("<![endif]-->").nl
      .w("<!--[if IE]>").nl
      .style.w(
          "#sidewalk form input[type=password] { font-family:sans-serif; }
           #sidewalk div.comment > h2 > a { display:none; }
           ").styleEnd
      .w("<![endif]-->").nl
      .headEnd

    // body
    out.body
    out.nl.w("<!-- Header -->").nl
    out.div("id='header'")
    out.h1.a(`/`).w("Project Haystack").aEnd.h1End
    hasFolio := Folio.isInstalled

    // header - nav bar
    out.ul("class='nav'")
    navItem(r, "index",    `/`,            "Home")
    navItem(r, "about",    `/about`,       "About")
    navItem(r, "doc",      `/doc`,         "Docs")
    navItem(r, "tag",      `/tag`,         "Tags")
    if (hasFolio)
    {
      navItem(r, "blog",     `/forum/blog`,  "Blog")
      navItem(r, "topic",    `/forum/topic`, "Forum")
    }
    navItem(r, "download", `/download`,    "Downloads")
    out.ulEnd.nl

    // user and login
    out.ul("class='user'")
    if (!hasFolio)
    {
      out.li.w("Login Disabled").liEnd
    }
    else if (user == null)
    {
      out.li.a(r.sys.userMod.loginUri).w("Login").aEnd.liEnd
      out.li.a(r.sys.userMod.signupUri).w("Signup").aEnd.liEnd
    }
    else
    {
      out.li.w(user.dis.toXml).liEnd
      if (user.isAdmin) out.li.a(`/admin`).w("Admin").aEnd.liEnd
      out.li.a(r.sys.userMod.settingsUri).w("Settings").aEnd.liEnd
      out.li.a(r.sys.userMod.logoutUri).w("Logout").aEnd.liEnd
    }
    out.ulEnd

    // search
    // google custom search - look and feel, options controlled:
    // https://www.google.com/cse/lookandfeel/customize?cx=011794689579947692868%3Agpuqp0n4zfq
    out.div("class='search'")
    out.w("""<script>
              (function() {
                var cx = '011794689579947692868:gpuqp0n4zfq';
                var gcse = document.createElement('script');
                gcse.type = 'text/javascript';
                gcse.async = true;
                gcse.src = (document.location.protocol == 'https:' ? 'https:' : 'http:') +
                    '//www.google.com/cse/cse.js?cx=' + cx;
                var s = document.getElementsByTagName('script')[0];
                s.parentNode.insertBefore(gcse, s);
              })();
             </script>
             <gcse:searchbox-only></gcse:searchbox-only>""")
    out.divEnd

    // close out header div
    out.divEnd

    // open content div
    out.nl.w("<!-- Content -->").nl
    out.div("id='content'").nl
  }

  private Void navItem(Renderer r, Str name, Uri uri, Str dis, Bool groupStart := false)
  {
    // figure out name of active name
    activeName := r.req.uri.path.getSafe(0) ?: "index"
    if (activeName == "forum")
      activeName = r.req.uri.path.getSafe(1) ?: "topic"

    attr := name == activeName ? "id='header-active-tab'" : ""
    if (groupStart) attr += " class='groupStart'"
    r.out.li(attr).a(uri).w(dis).aEnd.liEnd
  }

  override Void writeEnd(Renderer r)
  {
    hasFolio := Folio.isInstalled

    // close content div
    out := r.out
    out.divEnd

    // footer
    out.nl.w("<!-- Footer -->").nl
    out.div("id='footer'")
    out.ul
    out.li.a(`/`).w("Home").aEnd.liEnd
    out.li.a(`/about`).w("About").aEnd.liEnd
    out.li.a(`/doc`).w("Docs").aEnd.liEnd
    out.li.a(`/tag`).w("Tags").aEnd.liEnd
    if (hasFolio)
    {
      out.li.a(`/forum/blog`).w("Blog").aEnd.liEnd
      out.li.a(`/forum/topic`).w("Forum").aEnd.liEnd
    }
    out.li.a(`/download`).w("Downloads").aEnd.liEnd
    out.ulEnd
    out.p.w("All content licensed under the ").a(`/doc/License`).w("AFL 3.0").aEnd.pEnd
    out.divEnd

    out.nl.bodyEnd.htmlEnd
  }
}

