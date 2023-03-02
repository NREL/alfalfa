import {
  GraphQLBoolean,
  GraphQLFloat,
  GraphQLInt,
  GraphQLList,
  GraphQLNonNull,
  GraphQLObjectType,
  GraphQLSchema,
  GraphQLString
} from "graphql";

import resolvers from "./resolvers";

const tagType = new GraphQLObjectType({
  name: "Tag",
  description: "A Haystack tag",
  fields: () => ({
    key: {
      type: GraphQLString,
      description: "The key associated with a Haystack tag"
    },
    value: {
      type: GraphQLString,
      description: "The value if any associated with a Haystack tag"
    }
  })
});

const pointType = new GraphQLObjectType({
  name: "Point",
  description: "A Haystack point",
  fields: () => ({
    dis: {
      type: GraphQLString,
      description: "The value of the haystack dis tag"
    },
    tags: {
      type: new GraphQLList(tagType),
      description: "A list of the Haystack tags associated with the point"
    }
  })
});

const siteType = new GraphQLObjectType({
  name: "Site",
  description: "A site corresponding to an osm file upload",
  fields: () => ({
    name: {
      type: GraphQLString,
      description: "The name of the site, corresponding to the haystack siteRef display name"
    },
    siteRef: {
      type: GraphQLString,
      description: "A unique identifier, corresponding to the haystack siteRef value"
    },
    simStatus: {
      type: GraphQLString,
      description: "The status of the site simulation"
    },
    simType: {
      type: GraphQLString,
      description: "The type of simulation, osm or fmu"
    },
    datetime: {
      type: GraphQLString,
      description: "The current simulation time"
    },
    step: {
      type: GraphQLString,
      description: "The current simulation step"
    },

    points: {
      type: new GraphQLList(pointType),
      description: "A list of the Haystack points associated with the site",
      args: {
        writable: { type: GraphQLBoolean },
        cur: { type: GraphQLBoolean }
      },
      resolve: (site, args, context) => {
        return resolvers.sitePointResolver(site.siteRef, args, context);
      }
    }
  })
});

const simType = new GraphQLObjectType({
  // TODO: need/should rename this to simulation. No reason to keep the names short.
  name: "Sim",
  description: "A completed simulation, including any that may have stopped with errors.",
  fields: () => ({
    id: {
      type: GraphQLString,
      description: "A unique identifier for the simulation"
    },
    siteRef: {
      type: GraphQLString,
      description: "An identifier, corresponding to the haystack siteRef value"
    },
    simStatus: {
      type: GraphQLString,
      description: "The simulation status."
    },
    s3Key: {
      type: GraphQLString,
      description: "The s3 key where the simulation point is located."
    },
    name: {
      type: GraphQLString,
      description: "The site name."
    },
    url: {
      type: GraphQLString,
      description: "This is a signed url to the file download."
    },
    timeCompleted: {
      type: GraphQLString,
      description: "The date and time when the simulation was completed."
    },
    results: {
      type: GraphQLString,
      description:
        "Key simulation results, Can be interpreted as json, html, plain text depending on job type and use case."
    }
  })
});

const runType = new GraphQLObjectType({
  name: "Run",
  description: "A run",
  fields: () => ({
    id: {
      type: GraphQLString,
      description: "A unique identifier for the run"
    },
    sim_type: {
      type: GraphQLString,
      description: "The run simulation type"
    },
    status: {
      type: GraphQLString,
      description: "The run status"
    },
    created: {
      type: GraphQLString,
      description: "When the run was created"
    },
    modified: {
      type: GraphQLString,
      description: "When the run was last modified"
    },
    sim_time: {
      type: GraphQLString,
      description: "The current simulation time"
    },
    error_log: {
      type: GraphQLString,
      description: "The log of any errors in the Run"
    }
  })
});

const userType = new GraphQLObjectType({
  name: "User",
  description: "A person who uses our app",
  fields: () => ({
    //  id: globalIdField('User'),
    username: {
      type: GraphQLString,
      description: "The username of a person"
    },
    sites: {
      type: new GraphQLList(siteType),
      description: "The Haystack sites",
      args: {
        siteRef: { type: GraphQLString }
      },
      resolve: (user, { siteRef }, context) => {
        //return ['site a', 'site b', 'site c']},
        return resolvers.sitesResolver(user, siteRef, context);
      }
    },
    runs: {
      type: runType,
      description: "The Alfalfa Runs",
      args: {
        run_id: { type: GraphQLString }
      },
      resolve: (user, { run_id }, context) => {
        return resolvers.runResolver(user, run_id, context);
      }
    },
    sims: {
      type: new GraphQLList(simType),
      description: "The simulations",
      args: {
        siteRef: { type: GraphQLString },
        simRef: { type: GraphQLString }
      },
      resolve: (user, args, context) => {
        return resolvers.simsResolver(user, args, context);
      }
    }
  })
});

const queryType = new GraphQLObjectType({
  name: "Query",
  fields: () => ({
    viewer: {
      type: userType,
      resolve: (_, args, request) => {
        return { username: "" };
      }
    }
  })
});

const mutationType = new GraphQLObjectType({
  name: "Mutations",
  fields: () => ({
    runSim: {
      name: "RunSim",
      type: GraphQLString,
      args: {
        uploadFilename: { type: new GraphQLNonNull(GraphQLString) },
        uploadID: { type: new GraphQLNonNull(GraphQLString) }
      },
      resolve: (_, args, context) => {
        resolvers.runSimResolver(args.uploadFilename, args.uploadID, context);
      }
    },
    addSite: {
      name: "AddSite",
      type: GraphQLString,
      args: {
        modelName: { type: new GraphQLNonNull(GraphQLString) },
        uploadID: { type: new GraphQLNonNull(GraphQLString) }
      },
      resolve: (_, args, request) => {
        return resolvers.addSiteResolver(args.modelName, args.uploadID);
      }
    },
    runSite: {
      name: "RunSite",
      type: GraphQLString,
      args: {
        siteRef: { type: new GraphQLNonNull(GraphQLString) },
        startDatetime: { type: GraphQLString },
        endDatetime: { type: GraphQLString },
        timescale: { type: GraphQLFloat },
        realtime: { type: GraphQLBoolean },
        externalClock: { type: GraphQLBoolean }
      },
      resolve: (_, args, context) => {
        resolvers.runSiteResolver(args, context);
      }
    },
    stopSite: {
      name: "StopSite",
      type: GraphQLString,
      args: {
        siteRef: { type: new GraphQLNonNull(GraphQLString) }
      },
      resolve: (_, args, context) => {
        resolvers.stopSiteResolver(args, context);
      }
    },
    removeSite: {
      name: "removeSite",
      type: GraphQLString,
      args: {
        siteRef: { type: new GraphQLNonNull(GraphQLString) }
      },
      resolve: (_, args, request) => {
        resolvers.removeSiteResolver(args);
      }
    },
    advance: {
      name: "advance",
      type: GraphQLString,
      args: {
        siteRefs: { type: new GraphQLList(new GraphQLNonNull(GraphQLString)) }
      },
      resolve: (_, { siteRefs, time }, { advancer }) => {
        return resolvers.advanceResolver(advancer, siteRefs);
      }
    },
    writePoint: {
      name: "WritePoint",
      type: GraphQLString,
      args: {
        siteRef: { type: new GraphQLNonNull(GraphQLString) },
        pointName: { type: new GraphQLNonNull(GraphQLString) },
        value: { type: GraphQLFloat },
        level: { type: GraphQLInt }
      },
      resolve: (_, { siteRef, pointName, value, level }, context) => {
        return resolvers.writePointResolver(context, siteRef, pointName, value, level);
      }
    }
  })
});

export const schema = new GraphQLSchema({
  query: queryType,
  // Uncomment the following after adding some mutation fields:
  mutation: mutationType
});
