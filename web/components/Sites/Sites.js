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
import {Table, TableBody, TableHeader, TableFooter, TableHeaderColumn, TableRow, TableRowColumn} from 'material-ui/Table';

class Sites extends React.Component {

  state = {
    selected: [],
    startDisabled: true,
  };

  isSelected = (index) => {
    return this.state.selected.indexOf(index) !== -1;
  };

  handleRowSelection = (selectedRows) => {
    this.setState({
      selected: selectedRows,
      startDisabled: (selectedRows.length == 0)
    });
  };

  onStartSimClick = () => {
    if (this.state.selected.length > 0) {
      this.props.startSimProp(this.props.data.viewer.sites[this.state.selected[0]]);
    }
  }

  render() {
    if( ! this.props.data.loading ) {
      return (
        <div className={styles.root}>
          <Table onRowSelection={this.handleRowSelection}>
            <TableHeader>
              <TableRow>
                <TableHeaderColumn>Name</TableHeaderColumn>
                <TableHeaderColumn>Site Reference</TableHeaderColumn>
                <TableHeaderColumn>Status</TableHeaderColumn>
              </TableRow>
            </TableHeader>
            <TableBody deselectOnClickaway={false}>
              {this.props.data.viewer.sites.map((site, i) => {
                 return (
                  <TableRow key={site} selected={this.isSelected(i)}>
                    <TableRowColumn>{site}</TableRowColumn>
                    <TableRowColumn>{site}</TableRowColumn>
                    <TableRowColumn>Status</TableRowColumn>
                  </TableRow>
                 );
              })}
            </TableBody>
            <TableFooter>
              <TableRow>
                <TableRowColumn>
                  <RaisedButton disabled={this.state.startDisabled} label='Start Simulation' onClick={this.onStartSimClick}></RaisedButton>
                </TableRowColumn>
              </TableRow>
            </TableFooter>
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

const startSimQL = gql`
  mutation startSimulationMutation($siteRef: String!) {
    startSimulation(siteRef: $siteRef)
  }
`;

export default graphql(startSimQL, {
  props: ({ mutate }) => ({
    startSimProp: (siteRef) => mutate({ variables: { siteRef } }),
  })
})(graphql(sitesQL, {options: { pollInterval: 1000 },})(Sites));

