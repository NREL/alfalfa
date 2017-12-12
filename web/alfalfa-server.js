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
import HDict from 'nodehaystack/HDict';
import {MongoClient} from 'mongodb';
import uuid from 'uuid/v1';

var HBool = hs.HBool,
    HDateTime = hs.HDateTime,
    HDictBuilder = hs.HDictBuilder,
    //HDict = hs.HDict,
    HGrid = hs.HGrid,
    HWatch = hs.HWatch,
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

    for (var i = 0; i < 17; ++i) {
      this.val[i] = null;
      this.who[i] = null;
    }
  }
};

class AlfalfaWatch extends HWatch {
  constructor(db, id, dis, lease) {
    console.log('create watch');
    super();

    this._db = db;
    this._dis = null;
    this._lease = HNum.make(60,'min');

    this.watches = this._db.db.collection('watches');

    if( id ) {
      this._id = id;
    } else {
      this._id = uuid();
      this._dis = dis;
      this._lease = lease;
    }
  }

  id() {
    return this._id;
  }

  dis() {
    return this._dis;
  }

  lease() {
    return this._lease;
  }

  watchReadByIds(recs,ids,callback) {
    console.log('watchReadByIds');
    if (recs.length>=ids.length) {
      let b = new HGridBuilder();
      let meta = new HDictBuilder();
      console.log('create grid for id: ', this._id);
      console.log('create grid for lease: ', this._lease);
      meta.add('watchId',this._id);
      meta.add('lease',this._lease.val, this._lease.unit);
      callback(null, HGridBuilder.dictsToGrid(recs,meta.toDict()));
    } else {
      this._db.readById(ids[recs.length], false, (err, rec) => {
        recs[recs.length] = rec;
        this.watchReadByIds(recs, ids, callback);
      })
    }
  }

  sub(ids,callback) {
    console.log('sub');
    this.watches.findOne({ "_id": this._id }).then((watch) => {
      if (watch) {
        this._dis = watch.dis;
        this._lease = watch.lease;
        this.watches.updateOne(
          { "_id": this._id },
          { $addToSet: {"subs": ids} }
        ).then(() => {
            this.watchReadByIds([],ids,callback);
          });
      } else {
        const _watch = {
          "_id": this._id,
          "lease": this._lease,
          "dis": this._dis,
          "subs": ids
        };
        this.watches.insertOne(_watch).then(() => {
          this.watchReadByIds([],ids,callback);
        });
      }
    })
  }

  pollChanges(callback) {
    console.log('pollChanges');
    this.watches.findOne({ "_id": this._id }).then((watch) => {
      if (watch) {
        this._dis = watch.dis;
        this._lease = watch.lease;
        this.watchReadByIds([],watch.subs,callback);
      } else {
        callback(null,HGrid.EMPTY);
      }
    }).catch((err) => {
      callback(err);
    });
  }

  pollRefresh(callback) {
    console.log('pollRefresh');
    this.watches.findOne({ "_id": this._id }).then((watch) => {
      if (watch) {
        this._dis = watch.dis;
        this._lease = watch.lease;
        this.watchReadByIds([],watch.subs,callback);
      } else {
        callback(null,HGrid.EMPTY);
      }
    }).catch((err) => {
      callback(err);
    });
  }
};

/**
 * TestDatabase provides a simple implementation of
 * HDatabase with some test entities.
 * @constructor
 */
class AlfalfaServer extends HServer {
  constructor(mongodb) {
    super();

    this.db = mongodb
    this.writearrays = this.db.collection('writearrays');
    this.mrecs = this.db.collection('recs');
    this.recs = {};
  }

  recToDict(rec) {
    const keys = Object.keys(rec);
    var db = new HDictBuilder();
    for (let j = 0; j < keys.length; j++) {
      const key = keys[j];
      const r = new HJsonReader(rec[key]);
      try {
        const val = r.readScalar();
        db.add(key,val);
      }
      catch(err) {
        console.log(err);
      }
    }
    return db.toDict();
  }
  
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
      HStdOps.invokeAction,
      HStdOps.watchSub,
      HStdOps.watchUnsub,
      HStdOps.watchPoll
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
    this.mrecs.findOne({_id: id.val}).then((doc) => {
      if( doc ) {
        let dict = this.recToDict(doc.rec);
        callback(null,dict);
      } else {
        callback(null);
      }
    }).catch((err) => {
      callback(err);
    });
  };
  
  iterator(callback) {
    let self = this;
    this.mrecs.find().toArray().then((array) => {
      let index = 0;
      let length = array.length;

      let it = {
        next: function() {
          var dict;
          if (!this.hasNext()) {
            return null;
          }
          dict = self.recToDict(array[index].rec);
          index++;
          return dict;
        },
        hasNext: function() {
          return index < length;
        }
      };
      callback(null,it);
    }).catch((err) => {
      console.log(err);
      const it = {
        next: function() {
          return null;
        },
        hasNext: function() {
          return false;
        }
      };
      callback(null,it);
      //const a = [];
      //return a;
    });

    //var index = 0;
    //var length = docs.length;

    //console.log('boom 2');
    //return {
    //  next: function() {
    //    var dict;
    //    if (!this.hasNext()) {
    //      return null;
    //    }
    //    dict = this.recToDict(docs[index].rec);
    //    index++;
    //    return dict;
    //  },
    //  hasNext: function() {
    //    return index < length;
    //  }
    //};

    //callback(null, this._iterator());
  };

  //_iterator() {
  //  var docs = this.mrecs.find().toArray().then((array) => {
  //    console.log('boom 1');
  //    return array;
  //  }).catch(() => {
  //    const a = [];
  //    return a;
  //  });

  //  var index = 0;
  //  var length = docs.length;

  //  console.log('boom 2');
  //  return {
  //    next: function() {
  //      var dict;
  //      if (!this.hasNext()) {
  //        return null;
  //      }
  //      dict = this.recToDict(docs[index].rec);
  //      index++;
  //      return dict;
  //    },
  //    hasNext: function() {
  //      return index < length;
  //    }
  //  };
  //};
  
  //////////////////////////////////////////////////////////////////////////
  //Navigation
  //////////////////////////////////////////////////////////////////////////
  
  onNav(navId, callback) {
    const _onNav = (base, callback) => {
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

    if (typeof(navId) !== 'undefined' && navId !== null) {
      this.readById(HRef.make(navId), (err, base) => {
      //this.readById(navId, (err, base) => {
        if (err) {
          callback(err)
        } else {
          _onNav(base, callback);
        }
      });
    } else {
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
  
  onWatchOpen(dis, lease) {
    console.log('onWatchOpen');
    let w = new AlfalfaWatch(this,null,dis,lease);
    return w;
  };
  
  onWatches(callback) {
    console.log('onWatches');
    //callback(new Error("Unsupported Operation"));
  };
  
  onWatch(id) {
    console.log('onWatch');
    let w = new AlfalfaWatch(this,id,null,null);
    return w;
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
    
    for (var i = 0; i < array.val.length; ++i) {
      b.addRow([
        HNum.make(i + 1),
        HStr.make("" + (i + 1)),
        HNum.make(array.val[i]),
        HStr.make(array.who[i]),
      ]);
    }

    return b;
  }

  onPointWriteArray(rec, callback) {
    this.writearrays.findOne({_id: rec.id().val}).then((array) => {
      if( array ) {
        const b = this.writeArrayToGrid(array);
        callback(null, b.toGrid());
      } else {
        let array = new WriteArray();
        array._id = rec.id().val;
        let siteRef = rec.get('siteRef',false);
        if( siteRef ) {
          array.siteRef = siteRef.val;
        }
        this.writearrays.insertOne(array).then(() => {
          const b = this.writeArrayToGrid(array);
          callback(null, b.toGrid());
        }).catch((err) => {
          callback(err);
        });
      }
    }).catch((err) => {
      callback(err);
    })
  };
  
  onPointWrite(rec, level, val, who, dur, opts, callback) {
    let writeArray = null;

    this.writearrays.findOne({_id: rec.id().val}).then((array) => {
      if( array ) {
        array.val[level - 1] = val.val;
        array.who[level - 1] = who;
        this.writearrays.updateOne(
          { "_id": array._id },
          { $set: { "val": array.val, "who": array.who } 
        }).then(() => {
          writeArray = array;
        }).catch((err) => {
          callback(err);
        });
      } else {
        let array = new WriteArray();
        array._id = rec.id().val;
        let siteRef = rec.get('siteRef',false);
        if( siteRef ) {
          array.siteRef = siteRef.val;
        }
        array.val[level - 1] = val.val;
        array.who[level - 1] = who;
        this.writearrays.insertOne(array).then(() => {
          writeArray = array;
        }).catch((err) => {
          callback(err);
        });
      }
    }).catch((err) => {
      callback(err);
    });

    if( writeArray ) {
      var params = {
       MessageBody: `{"id": "${rec.id()}", "op": "PointWrite", "level": "${level}", "val": "${val}"}`,
       QueueUrl: process.env.JOB_QUEUE_URL
      };

      sqs.sendMessage(params, (err, data) => {
        if (err) {
          callback(err);
        } else {
          console.log(data);           // successful response
          const b = this.writeArrayToGrid(writeArray);
          callback(null, b.toGrid());
        }
      });
    } else {
      callback();
    }
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
    console.log("-- invokeAction \"" + rec.id().val + "." + action + "\" " + args);

     let body = {"id": rec.id().val, "op": "InvokeAction", "action": action};

     for (var it = args.iterator(); it.hasNext();) {
       var entry = it.next();
       var name = entry.getKey();
       var val = entry.getValue();
         body[name] = val.val;
     }
     
     var params = {
      MessageBody: JSON.stringify(body),
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

module.exports = AlfalfaServer;

