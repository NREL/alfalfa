//
// Copyright (c) 2015, Shawn Jacobson
// Licensed under the Academic Free License version 3.0
//
// Ported from @see {@link https://bitbucket.org/brianfrank/haystack-java|Haystack Java Toolkit}
//
// History:
//   21 Mar 2015  Shawn Jacobson  Creation
//

import AWS from 'aws-sdk';
import os from 'os';
import fs from 'fs';
import hs from 'nodehaystack';
import {MongoClient} from 'mongodb';

var HBool = hs.HBool,
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
    HStdOps = hs.HStdOps,
    HJsonReader = hs.HJsonReader;

AWS.config.update({region: 'us-west-1'});
var sqs = new AWS.SQS();

class WriteArray {
  constructor() {
    this.val = [];
    this.who = [];
  }
};

/**
 * TestDatabase provides a simple implementation of
 * HDatabase with some test entities.
 * @constructor
 */
class Database extends HServer {
  constructor() {
    super();

    this.writeArrays = {};
    this.recs = {};

    fs.readFile('./haystack_report_haystack.json', 'utf8', (err, data) => {
        if (err) {
          console.log('Error parsing json points file: ',err); 
        } else {
          try {
            var points = JSON.parse(data);
            this.addPoints(points);
          } catch(err) {
            console.log(err);
          }
        }
    });
  }

  mongo() {
    return MongoClient.connect(process.env.MONGO_URL);
  }

  writearrays() {
    return this.mongo().then((db) => {
      return db.collection('writearrays');
    });
  }

  addPoints(points) {
    for (let i = 0; i < points.length; i++) {
      const point = points[i];
      const keys = Object.keys(point);
      var db = new HDictBuilder();
      //const id = HRef.make(point['id']);
      for (let j = 0; j < keys.length; j++) {
        const key = keys[j];
        const r = new HJsonReader(point[key]);
        try {
          const val = r.readScalar();
          db.add(key,val);
        }
        catch(err) {
          console.log(err);
        }
      }
      const d = db.toDict();
      this.recs[d.id()] = d;
    }
  }
  
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
    console.log('onReadById: ',id.val);
    callback(null, this.recs[id.val]);
  };
  
  iterator(callback) {
    callback(null, this._iterator());
  };

  _iterator() {
    var index = 0;
    var recs = this.recs;
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
  
  //////////////////////////////////////////////////////////////////////////
  //Navigation
  //////////////////////////////////////////////////////////////////////////
  
  onNav(navId, callback) {
    console.log('onNav navid: ',navId);
    const _onNav = (base, callback) => {
      console.log('_onNav');
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
      this.readAll(filter, (err, grid) => {
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
    };

    console.log('starting to check type');
    if (typeof(navId) !== 'undefined' && navId !== null) {
      console.log('navid defined');
      //console.log('navId: ',HRef.make(navId));
      console.log('going to readById');
      this.readById(HRef.make(navId), (err, base) => {
      //this.readById(navId, (err, base) => {
        if (err) {
          callback(err)
        } else {
          console.log('base id: ',base.id());
          _onNav(base, callback);
        }
      });
    } else {
      console.log('navid undefined');
      _onNav(null, callback);
    }
  };

  onNavReadByUri(uri, callback) {
    console.log("onNavReadByUri: " + uri);
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
  
  writeArrayToGrid(array) {
    let b = new HGridBuilder();
    b.addCol("level");
    b.addCol("levelDis");
    b.addCol("val");
    b.addCol("who");
    
    for (var i = 0; i < 17; ++i) {
      if( array.val[i] ) {
        b.addRow([
          HNum.make(i + 1),
          HStr.make("" + (i + 1)),
          array.val[i],
          HStr.make(array.who[i]),
        ]);
      } else {
        b.addRow([
          HNum.make(i + 1),
          HStr.make("" + (i + 1)),
          undefined,
          HStr.make(undefined),
        ]);
      }
    }

    return b;
  }

  onPointWriteArray(rec, callback) {
    this.writearrays().then((collection) => {
      return new Promise((resolve,reject) => {
        collection.findOne({_id: rec.id().val}).then((array) => {
          if( array ) {
            resolve(array);
          } else {
            let array = new WriteArray();
            array._id = rec.id().val;
            collection.insertOne(array).then(() => {
              resolve(array);
            }).catch(() => {
              reject();
            });
          }
        }).catch(() => {
          reject();
        })
      })
    }).then((array) => {
      const b = this.writeArrayToGrid(array);
      callback(null, b.toGrid());
    }).catch(() => {
      callback();
    });
  };
  
  onPointWrite(rec, level, val, who, dur, opts, callback) {
    this.writearrays().then((collection) => {
      return new Promise((resolve,reject) => {
        collection.findOne({_id: rec.id().val}).then((array) => {
          if( array ) {
            array.val[level - 1] = val.val;
            array.who[level - 1] = who;
            collection.updateOne(
              { "_id": array._id },
              { $set: { "val": array.val, "who": array.who } 
            }).then(() => {
              resolve(array);
            }).catch(() => {
              reject();
            });
          } else {
            let array = new WriteArray();
            array._id = rec.id().val;
            array.val[level - 1] = val.val;
            array.who[level - 1] = who;
            collection.insertOne(array).then(() => {
              resolve(array);
            }).catch(() => {
              reject();
            });
          }
        }).catch(() => {
          reject();
        });
      });
    }).then((array) => {
      var params = {
       MessageBody: `{"id": "${rec.id()}", "op": "PointWrite", "level": "${level}", "val": "${val}"}`,
       QueueUrl: process.env.JOB_QUEUE_URL
      };

      sqs.sendMessage(params, (err, data) => {
        if (err) {
          console.log(err, err.stack); // an error occurred
          callback();
        } else {
          console.log(data);           // successful response
          const b = this.writeArrayToGrid(array);
          callback(null, b.toGrid());
        }
      });
    }).catch(() => {
      callback();
    });

    //this.writearrays().then((collection) => {
    //  return new Promise((resolve,reject) => {
    //    collection.findOne({_id: rec.id()}).then((array) => {
    //      array.val[level - 1] = val;
    //      array.who[level - 1] = who;
    //      collection.updateOne(
    //        { "_id": array._id },
    //        { $set: { "val": array.val, "who": array.who } },
    //        (err, result) => {
    //          if(err) {
    //            console.log('updateOne:', err);
    //            reject(err);
    //          } else {
    //            console.log('updateOne:', array);
    //            resolve(array);
    //          }
    //        }
    //      );
    //    }).catch(() => {
    //      console.log('onPointWrite new WriteArray');
    //      let array = new WriteArray();
    //      array._id = rec.id();
    //      array.val[level - 1] = val;
    //      array.who[level - 1] = who;
    //      collection.insertOne(array, (err, result) => {
    //        if( err ) {
    //          reject(err);
    //        } else {
    //          resolve(array);
    //        }
    //      });
    //    });
    //  })
    //}).then((array) => {
    //  var params = {
    //   MessageBody: `{"id": "${rec.id()}", "op": "PointWrite", "level": "${level}", "val": "${val}"}`,
    //   QueueUrl: process.env.JOB_QUEUE_URL
    //  };

    //  sqs.sendMessage(params, function(err, data) {
    //    if (err) {
    //      console.log(err, err.stack); // an error occurred
    //      callback();
    //    } else {
    //      console.log(data);           // successful response

    //      let b = new HGridBuilder();
    //      b.addCol("level");
    //      b.addCol("levelDis");
    //      b.addCol("val");
    //      b.addCol("who");
  
    //      for (var i = 0; i < 17; ++i) {
    //        b.addRow([
    //          HNum.make(i + 1),
    //          HStr.make("" + (i + 1)),
    //          array.val[i],
    //          HStr.make(array.who[i]),
    //        ]);
    //      }

    //      callback(null, b.toGrid());
    //      //callback();
    //    }
    //  });
    //}).catch((err) => {
    //  console.log(err); // an error occurred
    //  callback();
    //});
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

    var params = {
     MessageBody: `{"id": "${rec.id()}", "op": "InvokeAction", "action": "${action}"}`,
     QueueUrl: process.env.JOB_QUEUE_URL
    };

    sqs.sendMessage(params, function(err, data) {
      if (err) {
        console.log(err, err.stack); // an error occurred
        callback(null, HGridBuilder.dictsToGrid([]));
      } else {
        console.log(data);           // successful response
        callback(null, HGridBuilder.dictsToGrid([]));
      }
    });
  };
}

module.exports = Database;

