import os from "node:os";
import hs from "nodehaystack";
import { v1 as uuidv1 } from "uuid";
import AlfalfaAPI from "./api";
import dbops, { NUM_LEVELS } from "./dbops";
import { getPointKey, mapRedisArray } from "./utils";

// The purpose of this file is to consolidate operations to the database
// in a single place. Clients may transform the data into and out of
// these functions for their own api purposes. ie Haystack api, REST api.
const {
  HBool,
  HDateTime,
  HDictBuilder,
  HGridBuilder,
  HHisItem,
  HJsonReader,
  HNum,
  HRef,
  HServer,
  HStdOps,
  HStr,
  HUri,
  HWatch
} = hs;

const EMPTY_HGRID = new HGridBuilder().toGrid();

class AlfalfaWatch extends HWatch {
  constructor(db, id, dis, lease) {
    super();

    this._db = db;
    this._dis = null;
    this._lease = null;

    this.watches = this._db.db.collection("watches");

    if (id) {
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

  watchReadByIds(recs, ids, callback) {
    if (recs.length >= ids.length) {
      const meta = new HDictBuilder();
      meta.add("watchId", this._id);
      meta.add("lease", this._lease.val, this._lease.unit);
      callback(null, HGridBuilder.dictsToGrid(recs, meta.toDict()));
    } else {
      this._db.readById(ids[recs.length], false, (err, rec) => {
        recs[recs.length] = rec;
        this.watchReadByIds(recs, ids, callback);
      });
    }
  }

  sub(ids, callback) {
    this.watches.findOne({ _id: this._id }).then((watch) => {
      if (watch) {
        this._dis = watch.dis;
        this._lease = watch.lease;
        this.watches.updateOne({ _id: this._id }, { $addToSet: { subs: { $each: ids } } }).then(() => {
          this.watchReadByIds([], ids, callback);
        });
      } else {
        const _watch = {
          _id: this._id,
          lease: this._lease,
          dis: this._dis,
          subs: ids
        };
        this.watches.insertOne(_watch).then(() => {
          this.watchReadByIds([], ids, callback);
        });
      }
    });
  }

  unsub(ids, callback) {
    this.watches
      .updateOne({ _id: this._id }, { $pull: { subs: { $in: ids } } })
      .then(() => {
        callback(null, EMPTY_HGRID);
      })
      .catch((err) => {
        callback(err);
      });
  }

  close(callback) {
    this.watches
      .deleteOne({ _id: this._id })
      .then(() => {
        callback(null, EMPTY_HGRID);
      })
      .catch((err) => {
        callback(err);
      });
  }

  pollChanges(callback) {
    this.watches
      .findOne({ _id: this._id })
      .then((watch) => {
        if (watch) {
          this._dis = watch.dis;
          this._lease = watch.lease;
          this.watchReadByIds([], watch.subs, callback);
        } else {
          callback(null, EMPTY_HGRID);
        }
      })
      .catch((err) => {
        callback(err);
      });
  }

  pollRefresh(callback) {
    this.watches
      .findOne({ _id: this._id })
      .then((watch) => {
        if (watch) {
          this._dis = watch.dis;
          this._lease = watch.lease;
          this.watchReadByIds([], watch.subs, callback);
        } else {
          callback(null, EMPTY_HGRID);
        }
      })
      .catch((err) => {
        callback(err);
      });
  }
}

/**
 * TestDatabase provides a simple implementation of
 * HDatabase with some test entities.
 * @constructor
 */
class AlfalfaServer extends HServer {
  constructor(mongodb, redis) {
    super();

    this.db = mongodb;
    this.redis = redis;
    this.sites = this.db.collection("site");
    this.mrecs = this.db.collection("recs");
    this.recs = {};
    this.api = new AlfalfaAPI(this.db, this.redis);
  }

  recToDict(rec) {
    // A record can exist in the database before it is part
    // of haystack, so check if rec is not none first.
    const db = new HDictBuilder();
    if (rec) {
      for (const [key, recValue] of Object.entries(rec)) {
        const r = new HJsonReader(recValue);
        try {
          const val = r.readScalar();
          db.add(key, val);
        } catch (err) {
          console.log(err);
        }
      }
    }

    return db.toDict();
  }

  //////////////////////////////////////////////////////////////////////////
  //Ops
  //////////////////////////////////////////////////////////////////////////

  ops(callback) {
    const operations = [
      HStdOps.about,
      HStdOps.formats,
      HStdOps.hisRead,
      HStdOps.nav,
      HStdOps.ops,
      HStdOps.pointWrite,
      HStdOps.read,
      HStdOps.watchPoll,
      HStdOps.watchSub,
      HStdOps.watchUnsub
    ];
    callback(null, operations);
    return operations;
  }

  hostName() {
    try {
      return os.hostname();
    } catch (e) {
      return "Unknown";
    }
  }

  onAbout(callback) {
    const aboutDict = new HDictBuilder()
      .add("serverName", this.hostName())
      .add("vendorName", "Lynxspring, Inc.")
      .add("vendorUri", HUri.make("http://www.lynxspring.com/"))
      .add("productName", "Node Haystack Toolkit")
      .add("productVersion", "2.0.0")
      .add("productUri", HUri.make("https://bitbucket.org/lynxspring/nodehaystack/"))
      .toDict();
    callback(null, aboutDict);
    return aboutDict;
  }

  //////////////////////////////////////////////////////////////////////////
  //Reads
  //////////////////////////////////////////////////////////////////////////

  onReadById(id, callback) {
    this.mrecs
      .findOne({ ref_id: id.val })
      .then((doc) => {
        if (doc) {
          let dict = this.recToDict(doc.rec);
          callback(null, dict);
        } else {
          callback(null);
        }
      })
      .catch((err) => {
        callback(err);
      });
  }

  iterator(callback) {
    let self = this;
    this.mrecs
      .find()
      .toArray()
      .then((array) => {
        let index = 0;
        let length = array.length;

        let it = {
          next: function () {
            if (!this.hasNext()) {
              return null;
            }
            const dict = self.recToDict(array[index].rec);
            ++index;
            return dict;
          },
          hasNext: function () {
            return index < length;
          }
        };
        callback(null, it);
      })
      .catch((err) => {
        console.log(err);
        const it = {
          next: function () {
            return null;
          },
          hasNext: function () {
            return false;
          }
        };
        callback(null, it);
        return it;
      });

    //var index = 0;
    //var length = docs.length;

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
  }

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
      let filter = "site";
      if (typeof base !== "undefined" && base !== null) {
        if (base.has("site")) {
          filter = `equip and siteRef==${base.id().toCode()}`;
        } else if (base.has("equip")) {
          filter = `point and equipRef==${base.id().toCode()}`;
        } else {
          filter = "navNoChildren";
        }
      }

      // read children of base record
      this.readAll(filter, (err, grid) => {
        if (err) callback(err);
        else {
          // add navId column to results
          let i;
          const rows = [];
          const it = grid.iterator();
          for (i = 0; it.hasNext(); ) {
            rows[i++] = it.next();
          }
          for (i = 0; i < rows.length; ++i) {
            rows[i] = new HDictBuilder().add(rows[i]).add("navId", rows[i].id().val).toDict();
          }
          callback(null, HGridBuilder.dictsToGrid(rows));
        }
      });
    };

    if (typeof navId !== "undefined" && navId !== null) {
      this.readById(HRef.make(navId), (err, base) => {
        //this.readById(navId, (err, base) => {
        if (err) {
          callback(err);
        } else {
          _onNav(base, callback);
        }
      });
    } else {
      _onNav(null, callback);
    }
  }

  onNavReadByUri(uri, callback) {
    // return null;
  }

  //////////////////////////////////////////////////////////////////////////
  //Watches
  //////////////////////////////////////////////////////////////////////////

  onWatchOpen(dis, lease) {
    return new AlfalfaWatch(this, null, dis, lease);
  }

  onWatches(callback) {
    callback(new Error("Unsupported Operation"));
  }

  onWatch(id) {
    return new AlfalfaWatch(this, id, null, null);
  }

  //////////////////////////////////////////////////////////////////////////
  //Point Write
  //////////////////////////////////////////////////////////////////////////

  // Return:
  //{ val: ,
  //  level:
  //}
  currentWinningValue(array) {
    for (let i = 0; i < array.val.length; ++i) {
      if (array.val[i]) {
        return {
          val: array.val[i],
          level: i + 1
        };
      }
    }

    return null;
  }

  writeArrayToGrid(array) {
    const gridBuilder = new HGridBuilder();
    gridBuilder.addCol("level");
    gridBuilder.addCol("levelDis");
    gridBuilder.addCol("val");
    gridBuilder.addCol("who");

    for (let i = 0; i < array.val.length; ++i) {
      const level = i + 1;
      const value = array.val[i] === null ? null : HNum.make(array.val[i]);
      gridBuilder.addRow([HNum.make(level), HStr.make(String(level)), value, HStr.make(array.who[i])]);
    }

    return gridBuilder.toGrid();
  }

  async onPointWriteArray(rec, callback) {
    const siteRef = rec.get("siteRef", {}).val;
    const id = rec.id().val;
    try {
      let array = await dbops.getWriteArray(siteRef, id, this.redis);

      if (array) {
        callback(
          null,
          this.writeArrayToGrid({
            val: array,
            who: new Array(NUM_LEVELS).fill(null)
          })
        );
      } else {
        array = new Array(NUM_LEVELS).fill("");
        const key = getPointKey(siteRef, id);
        await this.redis.rPush(key, array);

        await this.mrecs.updateOne(
          { ref_id: id },
          {
            $set: { "rec.writeStatus": "s:ok" },
            $unset: { "rec.writeVal": "", "rec.writeLevel": "", "rec.writeErr": "" }
          }
        );

        const grid = this.writeArrayToGrid({
          val: mapRedisArray(array),
          who: new Array(NUM_LEVELS).fill(null)
        });
        callback(null, grid);
        return grid;
      }
    } catch (err) {
      callback(err);
    }
  }

  onPointWrite(rec, level, val, who, dur, opts, callback) {
    const value = val ? val.val : null;
    const id = rec.id().val;
    const siteRef = rec.get("siteRef", {}).val;
    dbops
      .writePoint(id, siteRef, level, value, this.db, this.redis)
      .then((array) => {
        callback(null, this.writeArrayToGrid(array));
      })
      .catch((err) => {
        callback(err);
      });
  }

  //////////////////////////////////////////////////////////////////////////
  //History
  //////////////////////////////////////////////////////////////////////////

  onHisRead(entity, range, callback) {
    // generate dummy 15min data
    const acc = [];
    let ts = range.start;
    const unit = entity.get("unit");
    const isBool = entity.get("kind").val === "Bool";
    while (ts.compareTo(range.end) <= 0) {
      const val = isBool ? HBool.make(acc.length % 2 === 0) : HNum.make(acc.length, unit);
      const item = HHisItem.make(ts, val);
      if (ts !== range.start) {
        acc[acc.length] = item;
      }
      ts = HDateTime.make(ts.millis() + 15 * 60 * 1000, ts.tz);
    }

    callback(null, acc);
    return acc;
  }

  onHisWrite(rec, items, callback) {
    callback(new Error("Unsupported Operation"));
  }
}

module.exports = AlfalfaServer;
