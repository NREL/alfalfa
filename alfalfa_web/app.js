import React from "react";
import "@fontsource/material-icons";
import "@fontsource/roboto";
import "normalize.css/normalize.css";
import ReactDOM from "react-dom";
import { BrowserRouter } from "react-router-dom";
import { App } from "./components/App/App.js";

ReactDOM.render(
  <BrowserRouter>
    <App />
  </BrowserRouter>,
  document.getElementById("root")
);
