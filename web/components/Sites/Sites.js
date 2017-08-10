import React, { PropTypes } from 'react';
import IconButton from 'material-ui/IconButton';
import FileUpload from 'material-ui/svg-icons/file/file-upload';
import TextField from 'material-ui/TextField';
import FlatButton from 'material-ui/FlatButton';
import RaisedButton from 'material-ui/RaisedButton';
import 'normalize.css/normalize.css';
import styles from './Sites.scss';
import Paper from 'material-ui/Paper';
import {cyan500, red500, greenA200} from 'material-ui/styles/colors';
import { graphql } from 'react-apollo';
import gql from 'graphql-tag';
import {Table, TableBody, TableHeader, TableHeaderColumn, TableRow, TableRowColumn} from 'material-ui/Table';


class SiteComponent extends React.Component {
  constructor(props) {
    super(props);

    this.onStartSimClick = this.onStartSimClick.bind(this);
  }

  static propTypes = {
    siteRef: PropTypes.string,
  };

  render() {
    return(
      <TableRow key={this.props.siteRef}>
        <TableRowColumn>{this.props.siteRef}</TableRowColumn>
        <TableRowColumn><RaisedButton label='Start Simulation' onClick={this.onStartSimClick}></RaisedButton></TableRowColumn>
      </TableRow>
    )
  }

  onStartSimClick() {
    this.props.startSimProp(this.props.siteRef);
  }
}

const startSimQL = gql`
  mutation startSimulationMutation($siteRef: String!) {
    startSimulation(siteRef: $siteRef)
  }
`;

let Site = graphql(startSimQL, {
  props: ({ mutate }) => ({
    startSimProp: (siteRef) => mutate({ variables: { siteRef } }),
  }),
})(SiteComponent);

class Sites extends React.Component {

  constructor(props) {
    super(props);

    //this.props.sites = ['site 1','site 2','site 3'];

    this.state = {
      //modelFile: null,
      //weatherFile: null,
    };
  };

  static propTypes = {
    //className: PropTypes.string,
  };

  //static contextTypes = {
  //  authenticated: React.PropTypes.bool,
  //  user: React.PropTypes.object
  //};

  render() {
    if( ! this.props.data.loading ) {
      return (
        <div className={styles.root}>
          <Table selectable={false}>
            <TableBody displayRowCheckbox={false}>
              {this.props.data.viewer.sites.map((site) => {
                 return (
                   <Site key={site} siteRef={site}></Site>
                 );
              })}
            </TableBody>
          </Table>
        </div>
      );
    } else {
      return null;
    }
  }
}

const sitesQL = gql`
  query QueueQuery {
    viewer {
      username,
      sites
    }
  }
`;

export default graphql(sitesQL, {options: { pollInterval: 1000 },})(Sites);

