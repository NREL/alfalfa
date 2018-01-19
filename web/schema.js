/**
 *  Copyright (c) 2015, Facebook, Inc.
 *  All rights reserved.
 *
 *  This source code is licensed under the BSD-style license found in the
 *  LICENSE file in the root directory of this source tree. An additional grant
 *  of patent rights can be found in the PATENTS file in the same directory.
 */

import {
  GraphQLBoolean,
  GraphQLFloat,
  GraphQLID,
  GraphQLInt,
  GraphQLList,
  GraphQLNonNull,
  GraphQLObjectType,
  GraphQLSchema,
  GraphQLString,
} from 'graphql';

import resolvers from './resolvers';

var tagType = new GraphQLObjectType({
  name: 'Tag',
  description: 'A Haystack tag',
  fields: () => ({
    key: {
      type: GraphQLString,
      description: 'The key associated with a Haystack tag'
    },
    value: {
      type: GraphQLString,
      description: 'The value if any associated with a Haystack tag'
    }
  })
});

var pointType = new GraphQLObjectType({
  name: 'Point',
  description: 'A Haystack point',
  fields: () => ({
    dis: {
      type: GraphQLString,
      description: 'The value of the haystack dis tag'
    },
    tags: {
      type: new GraphQLList(tagType),
      description: 'A list of the Haystack tags associated with the point'
    }
  })
});

var siteType = new GraphQLObjectType({
  name: 'Site',
  description: 'A site corresponding to an osm file upload',
  fields: () => ({
    name: {
      type: GraphQLString,
      description: 'The name of the site, corresponding to the haystack siteRef display name'
    },
    siteRef: {
      type: GraphQLString,
      description: 'A unique identifier, corresponding to the haystack siteRef value'
    },
    simStatus: {
      type: GraphQLString,
      description: 'The status of the site simulation'
    },
    datetime: {
      type: GraphQLString,
      description: 'The current simulation time'
    },
    points: {
      type: new GraphQLList(pointType),
      description: 'A list of the Haystack points associated with the site',
      resolve: (site,args,request) => {
        return resolvers.sitePointResolver(site.siteRef);
      }
    }
  })
});

var userType = new GraphQLObjectType({
  name: 'User',
  description: 'A person who uses our app',
  fields: () => ({
  //  id: globalIdField('User'),
    username: {
      type: GraphQLString,
      description: 'The username of a person', 
    },
    sites: {
      type: new GraphQLList(siteType),
      description: 'The Haystack sites', 
      args: {
        siteRef: { type: GraphQLString }
      },
      resolve: (user,{siteRef},request) => {
        //return ['site a', 'site b', 'site c']},
        return resolvers.sitesResolver(user,siteRef);
      }
    }
  }),
});

var queryType = new GraphQLObjectType({
  name: 'Query',
  fields: () => ({
    viewer: {
      type: userType,
      resolve: (_,args,request) => {return {username: 'smith'}},
    }
  }),
});

const addJobMutation = new GraphQLObjectType({
  name: 'AddJob',
  type: GraphQLString,
  args: {
    modelFile : { type: new GraphQLNonNull(GraphQLString) },
  },
  resolve: (_,args,request) => {},
});

const mutationType = new GraphQLObjectType({
  name: 'Mutations',
  fields: () => ({
    addJob: { 
      name: 'AddJob',
      type: GraphQLString,
      args: {
        osmName : { type: new GraphQLNonNull(GraphQLString) },
        uploadID : { type: new GraphQLNonNull(GraphQLString) },
      },
      resolve: (_,args,request) => {
        resolvers.addJobResolver(args.osmName,args.uploadID);
      },
    },
    startSimulation: {
      name: 'StartSimulation',
      type: GraphQLString,
      args: {
        siteRef : { type: new GraphQLNonNull(GraphQLString) },
        startDatetime : { type: GraphQLString },
        endDatetime : { type: GraphQLString },
        timescale : { type: GraphQLFloat },
        realtime : { type: GraphQLString },
      },
      resolve: (_,args,request) => {
        resolvers.startSimulationResolver(args);
      },
    },
    stopSimulation: {
      name: 'StopSimulation',
      type: GraphQLString,
      args: {
        siteRef : { type: new GraphQLNonNull(GraphQLString) },
      },
      resolve: (_,args,request) => {
        resolvers.stopSimulationResolver(args);
      },
    },
    removeSite: {
      name: 'removeSite',
      type: GraphQLString,
      args: {
        siteRef : { type: new GraphQLNonNull(GraphQLString) },
      },
      resolve: (_,args,request) => {
        resolvers.removeSiteResolver(args);
      },
    }
  })
});

export var Schema = new GraphQLSchema({
  query: queryType,
  // Uncomment the following after adding some mutation fields:
  mutation: mutationType,
});

