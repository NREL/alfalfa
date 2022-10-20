const request = require("supertest");
const should = require("should");

agent = request("http://localhost:3000");

describe("Economizer simulation", function () {
  describe("GET /nav", function () {
    it("should return the supported operations", function (done) {
      agent
        .get("/nav")
        .set("Accept", "application/json")
        .expect("Content-Type", /json/)
        .expect(200)
        .expect((res) => {
          res.body.should.have.property("meta");
          res.body.meta.should.have.property("ver", "2.0");
          res.body.should.have.property("rows");
          res.body.rows[0].should.have.property("id", "r:Test_Building");
        })
        .end(done);
    });
  });

  describe("POST /read", function () {
    it("should return the expected points", function (done) {
      agent
        .post("/read")
        .set("Accept", "application/json")
        .send({ meta: { ver: "2.0" }, cols: [{ name: "filter" }], rows: [{ filter: "s:point" }] })
        .expect("Content-Type", /json/)
        .expect(200)
        .expect((res) => {
          res.body.rows.should.be.instanceof(Array);
        })
        .end(done);
    });
  });

  describe("POST /invokeAction", function () {
    this.timeout(100000);
    it("should start the simulation", function (done) {
      agent
        .post("/invokeAction")
        .set("Accept", "application/json")
        // Empty cols and rows does not seem agreeable
        .send({
          meta: { ver: "2.0", id: "r:Test_Building", action: "s:Start" },
          cols: [{ name: "foo" }],
          rows: [{ foo: "s:bar" }]
        })
        .expect("Content-Type", /json/)
        .expect(200, done);
    });
  });

  describe("POST /pointWrite", function () {
    this.timeout(100000);
    it("should return the current write array", function (done) {
      agent
        .post("/pointWrite")
        .set("Accept", "application/json")
        .send({
          meta: { ver: "2.0" },
          cols: [{ name: "id" }],
          rows: [{ id: "s:DataCenter_mid_ZN_6_ZN_Zone_Air_Heating_sp" }]
        })
        .expect("Content-Type", /json/)
        .expect(200)
        .expect((res) => {
          res.body.rows[5].should.have.property("level", "n:6");
        })
        .end(done);
    });
  });

  //describe('POST /pointWrite with value', function() {
  //  this.timeout(100000);
  //  it('should return an updated write array', function(done) {
  //    agent
  //    .post('/pointWrite')
  //    .set('Accept', 'application/json')
  //    .send({
  //      "meta": {
  //        "ver": "2.0"
  //      },
  //      "cols": [{"name": "id"},{"name": "level"},{"name": "val"},{"name": "who"},{"name": "duration"}],
  //      "rows": [{
  //          "id": "r:DataCenter_mid_ZN_6_ZN_Zone_Air_Heating_sp",
  //          "level": "n:6",
  //          "val": "n:100",
  //          "who": "s:",
  //          "duration": "s:"
  //      }]
  //    })
  //    .expect('Content-Type', /json/)
  //    .expect(200)
  //    .expect( (res) => {
  //      res.body.rows[5].should.have.property("level","n:6");
  //      res.body.rows[5].should.have.property("val","n:100")
  //    })
  //    .end(done);
  //  });
  //});
});
