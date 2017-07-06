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

//const addJobMutation = new GraphQLObjectType({
//  name: 'AddJob',
//  inputFields: {
//    fileName: { type: new GraphQLNonNull(GraphQLString) },
//    username: { type: new GraphQLNonNull(GraphQLString) },
//  },
//  outputFields: {
//    result: {
//      type: GraphQLString,
//      resolve: ({result}) => {
//        return result;
//      }
//    },
//  },
//
//  //mutateAndGetPayload: ({ fileName, username }) => addJob(fileName, username)
//});

var mutationType = new GraphQLObjectType({
  name: 'Mutation',
  fields: () => ({
    // Add your own mutations here
    addJob: addJobMutation, 
  })
});

export var Schema = new GraphQLSchema({
  query: queryType,
  // Uncomment the following after adding some mutation fields:
  //mutation: mutationType,
  //subscription: subscriptionType,
});

