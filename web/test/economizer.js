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

const request = require('supertest');
const should = require('should');

agent = request('http://localhost:3000');

describe('Economizer simulation', function() {
  describe('GET /nav', function() {
    it('should return the supported operations', function(done) {
      agent
      .get('/nav')
      .set('Accept', 'application/json')
      .expect('Content-Type', /json/)
      .expect(200)
      .expect( (res) => {
        res.body.should.have.property("meta");
        res.body.meta.should.have.property("ver", "2.0");
        res.body.should.have.property("rows");
        res.body.rows[0].should.have.property("id", "r:Test_Building");
      })
      .end(done);
    });
  });

  describe('POST /read', function() {
    it('should return the expected points', function(done) {
      agent
      .post('/read')
      .set('Accept', 'application/json')
      .send({"meta": {"ver": "2.0"},
        "cols": [{"name": "filter"}],
        "rows": [{"filter": "s:point"}]
      })
      .expect('Content-Type', /json/)
      .expect(200)
      .expect( (res) => {
        res.body.rows.should.be.instanceof(Array)
      })
      .end(done);
    });
  });

  describe('POST /invokeAction', function() {
    this.timeout(100000);
    it('should start the simulation', function(done) {
      agent
      .post('/invokeAction')
      .set('Accept', 'application/json')
      // Empty cols and rows does not seem agreeable
      .send({"meta": {"ver": "2.0", "id": "r:Test_Building", "action": "s:Start"},
        "cols": [{"name": "foo"}],
        "rows": [{"foo": "s:bar"}]
      })
      .expect('Content-Type', /json/)
      .expect(200,done)
    });
  });

  describe('POST /pointWrite', function() {
    this.timeout(100000);
    it('should return the current write array', function(done) {
      agent
      .post('/pointWrite')
      .set('Accept', 'application/json')
      .send({"meta": {"ver": "2.0"},
      "cols": [{"name": "id"}],
      "rows": [{"id": "s:DataCenter_mid_ZN_6_ZN_Zone_Air_Heating_sp"}]
      })
      .expect('Content-Type', /json/)
      .expect(200)
      .expect( (res) => {
        res.body.rows[5].should.have.property("level","n:6")
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
