import React from 'react';
import { Component } from 'react';
import styles from './App.scss';
import { Link, Route } from 'react-router-dom';
import IconButton from 'material-ui/IconButton';
import FileCloudQueue from 'material-ui/svg-icons/file/cloud-queue';
import FileCloudDone from 'material-ui/svg-icons/file/cloud-done';
import ActionAccountCircle from 'material-ui/svg-icons/action/account-circle';
import MuiThemeProvider from 'material-ui/styles/MuiThemeProvider';
import {Toolbar, ToolbarGroup, ToolbarSeparator, ToolbarTitle} from 'material-ui/Toolbar';
import Badge from 'material-ui/Badge';
import Upload from '../Upload/Upload.js';
//import TextField from 'material-ui/TextField';
//import RaisedButton from 'material-ui/RaisedButton';
//import IconMenu from 'material-ui/IconMenu';
//import MenuItem from 'material-ui/MenuItem';
//import gql from 'graphql-tag';
//import { graphql } from 'react-apollo';


const Queue = () => (
  <div>
    <h2>Queue</h2>
  </div>
);

const Home = () => (
  <div>
    <h2>Home</h2>
  </div>
);

class App extends React.Component {

  render() {
    return (
      <MuiThemeProvider>
        <div className={styles.root} >
          <Toolbar style={{height: '80px', alignItems: 'center'}} >
            <ToolbarTitle text="Alfalfa" onClick={this.onToolbarClick}/>
            <ToolbarGroup lastChild={true}>
              <Link to={'/queue'}>
                <IconButton onClick={this.onQueueClick}>
                  <FileCloudQueue />
                </IconButton>
              </Link>
            </ToolbarGroup>
          </Toolbar>
          <Route exact path="/" component={Upload}/>
          <Route path='/queue' component={Queue} />
        </div>
      </MuiThemeProvider>
    );
  }
}

export default App;

