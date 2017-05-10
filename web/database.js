//
// Copyright (c) 2015, Shawn Jacobson
// Licensed under the Academic Free License version 3.0
//
// Ported from @see {@link https://bitbucket.org/brianfrank/haystack-java|Haystack Java Toolkit}
//
// History:
//   21 Mar 2015  Shawn Jacobson  Creation
//

var hs = require('nodehaystack');

var os = require('os'),
    HBool = hs.HBool,
    HDateTime = hs.HDateTime,
    HDictBuilder = hs.HDictBuilder,
    HGrid = hs.HGrid,
    HHisItem = hs.HHisItem,
    HMarker = hs.HMarker,
    HNum = hs.HNum,
    HRef = hs.HRef,
    HStr = hs.HStr,
    HUri = hs.HUri,
    HGridBuilder = hs.HGridBuilder,
    HServer = hs.HServer,
    HStdOps = hs.HStdOps;

/**
 * TestDatabase provides a simple implementation of
 * HDatabase with some test entities.
 * @constructor
 */
class TestDatabase extends HServer {
  constructor() {
    super();
    this.writeArrays = {};
    this.WriteArray = function() {
      this.val = [];
      this.who = [];
    };

    this.recs = {};
    this.addSite("A", "Richmond", "VA", 1000);
    this.addSite("B", "Richmond", "VA", 2000);
    this.addSite("C", "Washington", "DC", 3000);
    this.addSite("D", "Boston", "MA", 4000);
    this.addSite("E", "St. Louis", "MO", 5000);
  }
  //TestDatabase.prototype = Object.create(HServer.prototype);
  //TestDatabase.prototype = Object.create(null);
  //module.exports.TestDatabase = TestDatabase;
  //module.exports = TestDatabase;
  
  addSite(dis, geoCity, geoState, area) {
    var site = new HDictBuilder()
        .add("id", HRef.make(dis))
        .add("dis", dis)
        .add("site", HMarker.VAL)
        .add("geoCity", geoCity)
        .add("geoState", geoState)
        .add("geoAddr", "" + geoCity + "," + geoState)
        .add("tz", "New_York")
        .add("area", HNum.make(area, "ft\u00B2"))
        .toDict();
    this.recs[dis] = site;
  
    this.addMeter(site, dis + "-Meter");
    this.addAhu(site, dis + "-AHU1");
    this.addAhu(site, dis + "-AHU2");
  };
  
  addMeter(site, dis) {
    HServer.call(this);
    var equip = new HDictBuilder()
        .add("id", HRef.make(dis))
        .add("dis", dis)
        .add("equip", HMarker.VAL)
        .add("elecMeter", HMarker.VAL)
        .add("siteMeter", HMarker.VAL)
        .add("siteRef", site.get("id"))
        .toDict();
    this.recs[dis] = equip;
    this.addPoint(equip, dis + "-KW", "kW", "elecKw");
    this.addPoint(equip, dis + "-KWH", "kWh", "elecKwh");
  };
  
  addAhu(site, dis) {
    var equip = new HDictBuilder()
        .add("id", HRef.make(dis))
        .add("dis", dis)
        .add("equip", HMarker.VAL)
        .add("ahu", HMarker.VAL)
        .add("siteRef", site.get("id"))
        .toDict();
    this.recs[dis] = equip;
    this.addPoint(equip, dis + "-Fan", null, "discharge air fan cmd");
    this.addPoint(equip, dis + "-Cool", null, "cool cmd");
    this.addPoint(equip, dis + "-Heat", null, "heat cmd");
    this.addPoint(equip, dis + "-DTemp", "\u00B0F", "discharge air temp sensor");
    this.addPoint(equip, dis + "-RTemp", "\u00B0F", "return air temp sensor");
    this.addPoint(equip, dis + "-ZoneSP", "\u00B0F", "zone air temp sp writable");
  };
  
  addPoint(equip, dis, unit, markers) {
    var b = new HDictBuilder()
        .add("id", HRef.make(dis))
        .add("dis", dis)
        .add("point", HMarker.VAL)
        .add("his", HMarker.VAL)
        .add("siteRef", equip.get("siteRef"))
        .add("equipRef", equip.get("id"))
        .add("kind", typeof(unit) === 'undefined' || unit === null ? "Bool" : "Number")
        .add("tz", "New_York");
    if (typeof(unit) !== 'undefined' && unit !== null) {
      b.add("unit", unit);
      if (unit === 'kW') {
        b.add("power", HMarker.VAL);
        b.add("siteMeter", HMarker.VAL);
      }
    }
    var st = markers.split(" ");
    for (var i = 0; i < st.length; i++) {
      b.add(st[i]);
    }
    this.recs[dis] = b.toDict();
  };
  
  //////////////////////////////////////////////////////////////////////////
  //Ops
  //////////////////////////////////////////////////////////////////////////
  
  ops(callback) {
    callback(null, [
      HStdOps.about,
      HStdOps.ops,
      HStdOps.formats,
      HStdOps.read,
      HStdOps.nav,
      HStdOps.pointWrite,
      HStdOps.hisRead,
      HStdOps.invokeAction
    ]);
  };
  
  hostName() {
    try {
      return os.hostname();
    }
    catch (e) {
      return "Unknown";
    }
  };
  
  onAbout(callback) {
    var aboutdict = new HDictBuilder()
        .add("serverName", this.hostName())
        .add("vendorName", "Lynxspring, Inc.")
        .add("vendorUri", HUri.make("http://www.lynxspring.com/"))
        .add("productName", "Node Haystack Toolkit")
        .add("productVersion", "2.0.0")
        .add("productUri", HUri.make("https://bitbucket.org/lynxspring/nodehaystack/"))
        .toDict();
    callback(null, aboutdict);
  };
  
  //////////////////////////////////////////////////////////////////////////
  //Reads
  //////////////////////////////////////////////////////////////////////////
  
  onReadById(id, callback) {
    callback(null, this.recs[id.val]);
  };
  
  iterator(callback) {
    var _iterator = function(self) {
      var index = 0;
      var recs = self.recs;
      var keys = Object.keys(recs);
      var length = keys.length;
      return {
        next: function() {
          var elem;
          if (!this.hasNext()) {
            return null;
          }
          elem = recs[keys[index]];
          index++;
          return elem;
        },
        hasNext: function() {
          return index < length;
        }
      };
    };
    callback(null, _iterator(this));
  };
  
  //////////////////////////////////////////////////////////////////////////
  //Navigation
  //////////////////////////////////////////////////////////////////////////
  
  onNav(navId, callback) {
    var self = this;
    // test database navId is record id
    if (typeof(navId) !== 'undefined' && navId !== null) {
      self.readById(HRef.make(navId), function(err, base) {
        if (err) callback(err)
        else _onNav(self, base, callback);
      });
    } else {
      // map base record to site, equip, or point
      var filter = "site";
      if (typeof(base) !== 'undefined' && base !== null) {
        if (base.has("site")) {
          filter = "equip and siteRef==" + base.id().toCode();
        }
        else if (base.has("equip")) {
          filter = "point and equipRef==" + base.id().toCode();
        }
        else {
          filter = "navNoChildren";
        }
      }
  
      // read children of base record
      self.readAll(filter, function(err, grid) {
        if (err) callback(err);
        else {
          // add navId column to results
          var i;
          var rows = [];
          var it = grid.iterator();
          for (i = 0; it.hasNext();) {
            rows[i++] = it.next();
          }
          for (i = 0; i < rows.length; ++i) {
            rows[i] = new HDictBuilder().add(rows[i]).add("navId", rows[i].id().val).toDict();
          }
          callback(null, HGridBuilder.dictsToGrid(rows));
        }
      });
    }
  };

  onNavReadByUri(uri, callback) {
    // return null;
  };
  
  //////////////////////////////////////////////////////////////////////////
  //Watches
  //////////////////////////////////////////////////////////////////////////
  
  onWatchOpen(dis, lease, callback) {
    callback(new Error("Unsupported Operation"));
  };
  
  onWatches(callback) {
    callback(new Error("Unsupported Operation"));
  };
  
  onWatch(id, callback) {
    callback(new Error("Unsupported Operation"));
  };
  
  //////////////////////////////////////////////////////////////////////////
  //Point Write
  //////////////////////////////////////////////////////////////////////////
  
  onPointWriteArray(rec, callback) {
    var array = writeArrays[rec.id()];
    if (typeof(array)==='undefined' || array===null) {
      writeArrays[rec.id()] = array = new WriteArray();
    }
  
    var b = new HGridBuilder();
    b.addCol("level");
    b.addCol("levelDis");
    b.addCol("val");
    b.addCol("who");
  
    for (var i = 0; i < 17; ++i) {
      b.addRow([
        HNum.make(i + 1),
        HStr.make("" + (i + 1)),
        array.val[i],
        HStr.make(array.who[i]),
      ]);
    }
  
    callback(null, b.toGrid());
  };
  
  onPointWrite(rec, level, val, who, dur, opts, callback) {
    console.log("onPointWrite: " + rec.dis() + "  " + val + " @ " + level + " [" + who + "]");
    var array = writeArrays[rec.id()];
    if (typeof(array) === 'undefined' || array === null) {
      writeArrays[rec.id()] = array = new WriteArray();
    }
    array.val[level - 1] = val;
    array.who[level - 1] = who;
    callback();
  };
  
  //////////////////////////////////////////////////////////////////////////
  //History
  //////////////////////////////////////////////////////////////////////////
  
  onHisRead(entity, range, callback) {
    // generate dummy 15min data
    var acc = [];
    var ts = range.start;
    var unit = entity.get("unit");
    var isBool = entity.get("kind").val === "Bool";
    while (ts.compareTo(range.end) <= 0) {
      var val = isBool ?
          HBool.make(acc.length % 2 === 0) :
          HNum.make(acc.length, unit);
      var item = HHisItem.make(ts, val);
      if (ts !== range.start) {
        acc[acc.length] = item;
      }
      ts = HDateTime.make(ts.millis() + 15 * 60 * 1000, ts.tz);
    }
  
    callback(null, acc);
  };
  
  onHisWrite(rec, items, callback) {
    callback(new Error("Unsupported Operation"));
  };
  
  //////////////////////////////////////////////////////////////////////////
  //Actions
  //////////////////////////////////////////////////////////////////////////
  
  onInvokeAction(rec, action, args, callback) {
    console.log("-- invokeAction \"" + rec.dis() + "." + action + "\" " + args);
    callback(null, HGrid.EMPTY);
  };
}

module.exports = TestDatabase;

