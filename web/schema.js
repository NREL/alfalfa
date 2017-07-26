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

var userType = new GraphQLObjectType({
  name: 'User',
  description: 'A person who uses our app',
  fields: () => ({
  //  id: globalIdField('User'),
    username: {
      type: GraphQLString,
      description: 'The username of a person', 
    },
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
        fileName : { type: new GraphQLNonNull(GraphQLString) },
      },
      resolve: (_,args,request) => {
        console.log("AddJob", args)
        resolvers.addJobResolver(args.fileName);
      },
    }
  })
});

export var Schema = new GraphQLSchema({
  query: queryType,
  // Uncomment the following after adding some mutation fields:
  mutation: mutationType,
});

