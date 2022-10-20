import { ApolloClient, ApolloProvider, InMemoryCache } from "@apollo/client";
import "@fontsource/material-icons";
import "@fontsource/roboto";
import "normalize.css/normalize.css";
import React from "react";
import ReactDOM from "react-dom";
import { BrowserRouter } from "react-router-dom";
import App from "./components/App/App.js";

const client = new ApolloClient({
  uri: "/graphql",
  cache: new InMemoryCache()
});

ReactDOM.render(
  <ApolloProvider client={client}>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </ApolloProvider>,
  document.getElementById("root")
);
