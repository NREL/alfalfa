/***********************************************************************************************************************
*  Copyright (c) 2008-2018, Alliance for Sustainable Energy, LLC, and other contributors. All rights reserved.
*
*  Redistribution and use in source and binary forms, with or without modification, are permitted provided that the
*  following conditions are met:
*
*  (1) Redistributions of source code must retain the above copyright notice, this list of conditions and the following
*  disclaimer.
*
*  (2) Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following
*  disclaimer in the documentation and/or other materials provided with the distribution.
*
*  (3) Neither the name of the copyright holder nor the names of any contributors may be used to endorse or promote products
*  derived from this software without specific prior written permission from the respective party.
*
*  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDER(S) AND ANY CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
*  INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
*  DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER(S), ANY CONTRIBUTORS, THE UNITED STATES GOVERNMENT, OR THE UNITED
*  STATES DEPARTMENT OF ENERGY, NOR ANY OF THEIR EMPLOYEES, BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
*  EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
*  USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
*  STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
*  ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
***********************************************************************************************************************/

import AWS from 'aws-sdk';
import os from 'os';
import fs from 'fs';
import hs from 'nodehaystack';
import HDict from 'nodehaystack/HDict';
import { v1 as uuidv1 } from 'uuid';
import dbops from './dbops';

var HBool = hs.HBool,
    HDateTime = hs.HDateTime,
    HDictBuilder = hs.HDictBuilder,
    //HDict = hs.HDict,
    HGrid = hs.HGrid,
    HWatch = hs.HWatch,
    HHisItem = hs.HHisItem,
    HMarker = hs.HMarker,
  // The purpose of this file is to consolidate operations to the database
  // in a single place. Clients may transform the data into and out of 
  // these functions for their own api purposes. ie Haystack api, GraphQL api.
    HNum = hs.HNum,
    HRef = hs.HRef,
    HStr = hs.HStr,
    HUri = hs.HUri,
    HGridBuilder = hs.HGridBuilder,
    HServer = hs.HServer,
    HStdOps = hs.HStdOps,
    HJsonReader = hs.HJsonReader;

AWS.config.update({region: 'us-east-1'});
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
    super();

    this._db = db;
    this._dis = null;
    this._lease = null;

    this.watches = this._db.db.collection('watches');

    if( id ) {
      this._id = id;
    } else {
      this._id = uuidv1();
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
    if (recs.length>=ids.length) {
      let b = new HGridBuilder();
      let meta = new HDictBuilder();
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
    this.watches.findOne({ "_id": this._id }).then((watch) => {
      if (watch) {
        this._dis = watch.dis;
        this._lease = watch.lease;
        this.watches.updateOne(
          { "_id": this._id },
          { $addToSet: {"subs": {$each: ids} } }
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

  unsub(ids, callback) {
    this.watches.updateOne(
      { "_id": this._id },
      { "$pull": { "subs": { "$in": ids } } }
    ).then(() => {
      callback(null,HGrid.EMPTY);
    }).catch( (err) => {
      callback(err);
    });
  }

  close(callback) {
    this.watches.deleteOne({ "_id": this._id }).then( () => {
      callback(null,HGrid.EMPTY);
    }).catch( (err) => {
      callback(err);
    });
  }

  pollChanges(callback) {
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
  constructor(mongodb, redis, pub, sub) {
    super();

    this.db = mongodb;
    this.redis = redis;
    this.pub = pub;
    this.sub = sub;
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
    // return null;
  };
  
  //////////////////////////////////////////////////////////////////////////
  //Watches
  //////////////////////////////////////////////////////////////////////////
  
  onWatchOpen(dis, lease) {
    let w = new AlfalfaWatch(this,null,dis,lease);
    return w;
  };
  
  onWatches(callback) {
    callback(new Error("Unsupported Operation"));
  };
  
  onWatch(id) {
    let w = new AlfalfaWatch(this,id,null,null);
    return w;
  };
  
  //////////////////////////////////////////////////////////////////////////
  //Point Write
  //////////////////////////////////////////////////////////////////////////
  
  // Return:
  //{ val: ,
  //  level: 
  //}
  currentWinningValue(array) {
    for (var i = 0; i < array.val.length; ++i) {
      if( array.val[i] ) {
        return {
          val: array.val[i],
          level: i + 1
        }
      }
    }

    return null;
  }

  writeArrayToGrid(array) {
    let b = new HGridBuilder();
    b.addCol("level");
    b.addCol("levelDis");
    b.addCol("val");
    b.addCol("who");
    
    for (var i = 0; i < array.val.length; ++i) {
      if( array.val[i] || array.val[i] === 0 ) {
        b.addRow([
          HNum.make(i + 1),
          HStr.make("" + (i + 1)),
          HNum.make(array.val[i]),
          HStr.make(array.who[i]),
        ]);
      } else {
        b.addRow([
          HNum.make(i + 1),
          HStr.make("" + (i + 1)),
          null,
          HStr.make(array.who[i]),
        ]);
      }
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
        array.siteRef = rec.get('siteRef',{}).val;
        this.writearrays.insertOne(array).then( () => {
          return this.mrecs.updateOne(
            { "_id": array._id },
            { $set: { "rec.writeStatus": "s:ok" }, $unset: { "rec.writeVal": "", "rec.writeLevel": "", "rec.writeErr": ""} }
          )
        }).then( () => {
          const b = this.writeArrayToGrid(array);
          callback(null, b.toGrid());
        }).catch( (err) => {
          callback(err);
        });
      }
    }).catch((err) => {
      callback(err);
    })
  };
  
  onPointWrite(rec, level, val, who, dur, opts, callback) {
    const value = val ? val.val : null;
    const id = rec.id().val;
    const siteRef = rec.get('siteRef',{}).val;
    dbops.writePoint(id, siteRef, level, value, who, dur, this.db).then((array) => {
      const b = this.writeArrayToGrid(array);
      callback(null, b.toGrid());
    }).catch((err) => {
      callback(err);
    });
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
    if ( action == "runSite" ) {
      this.mrecs.updateOne(
        { _id: rec.id().val },
        { $set: { "rec.simStatus": "s:Starting" } }
      ).then( () => {
        let body = {"id": rec.id().val, "op": "InvokeAction", "action": action};

        for (var it = args.iterator(); it.hasNext();) {
          var entry = it.next();
          var name = entry.getKey();
          var val = entry.getValue();
            body[name] = val.val;
        }
     
        var params = {
         MessageBody: JSON.stringify(body),
         QueueUrl: process.env.JOB_QUEUE_URL,
         MessageGroupId: "Alfalfa"
        };

        sqs.sendMessage(params, function(err, data) {
          if (err) {
            console.log(err, err.stack); // an error occurred
            callback(null, HGridBuilder.dictsToGrid([]));
          } else {
            callback(null, HGridBuilder.dictsToGrid([]));
          }
        });
      })
    } else if ( action == "stopSite" ) {
      const siteRef = rec.id().val
      this.mrecs.updateOne(
        { _id: siteRef },
        { $set: { "rec.simStatus": "s:Stopping" } }
      ).then( () => {
        this.pub.publish(siteRef, "stop");
      });
      callback(null,HGrid.EMPTY);
    } else if ( action == "removeSite" ) {
      this.mrecs.deleteMany({site_ref: rec.id().val});
      this.writearrays.deleteMany({siteRef: rec.id().val});
      callback(null,HGrid.EMPTY);
    }
  };
}

module.exports = AlfalfaServer;

