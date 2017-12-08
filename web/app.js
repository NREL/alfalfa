import 'babel-polyfill';
import React from 'react';
import ReactDOM from 'react-dom';
import { BrowserRouter as Router, Route, HomeRoute, Redirect, Switch } from 'react-router-dom';
import injectTapEventPlugin from 'react-tap-event-plugin';
import ApolloClient, { createNetworkInterface, addTypename } from 'apollo-client';
import { ApolloProvider } from 'react-apollo';
//import Cookies from 'js-cookie';
import { createStore, combineReducers, applyMiddleware, compose } from 'redux';
import App from './components/App/App.js';
import 'typeface-roboto';

const networkInterface = createNetworkInterface({
   uri: '/graphql',
   opts: {
     credentials: 'same-origin',
   }
 });

const client = new ApolloClient({ 
  networkInterface: networkInterface,
  queryTransformer: addTypename,
});

const store = createStore(
  ///client.reducer(),
  //{}, // initial state
  compose(
      applyMiddleware(client.middleware()),
      // If you are using the devToolsExtension, you can add it here also
     window.devToolsExtension ? window.devToolsExtension() : f => f,
  )
);

injectTapEventPlugin();

ReactDOM.render(
  <ApolloProvider store={store} client={client}>
    <Router>
      <Route component={App} />
    </Router>
  </ApolloProvider>,
  document.getElementById('root')
);

