import React, { PropTypes } from 'react';
import IconButton from 'material-ui/IconButton';
import FileUpload from 'material-ui/svg-icons/file/file-upload';
import TextField from 'material-ui/TextField';
import FlatButton from 'material-ui/FlatButton';
import RaisedButton from 'material-ui/RaisedButton';
import Dialog from 'material-ui/Dialog';
import 'normalize.css/normalize.css';
import styles from './Sites.scss';
import {Card, CardActions, CardHeader, CardText} from 'material-ui/Card';
import {cyan500, red500, greenA200} from 'material-ui/styles/colors';
import { graphql } from 'react-apollo';
import gql from 'graphql-tag';
import {Table, TableBody, TableHeader, TableFooter, TableHeaderColumn, TableRow, TableRowColumn} from 'material-ui/Table';

class Point extends React.Component {

  render = () => {
    return(
      <div className={styles.pointRoot}>
        <Card >
          <CardHeader
            title={"Point " + this.props.point.dis}
            actAsExpander={true}
            showExpandableButton={true}
          />
          <CardText expandable={true}>
            <Table selectable={false}>
              <TableHeader displaySelectAll={false}>
                <TableRow selectable={false}>
                  <TableHeaderColumn>Key</TableHeaderColumn>
                  <TableHeaderColumn>Value</TableHeaderColumn>
                </TableRow>
              </TableHeader>
              <TableBody displayRowCheckbox={false}>
                  {this.props.point.tags.map((tag) => {
                     return (
                      <TableRow key={tag.key}>
                        <TableRowColumn>{tag.key}</TableRowColumn>
                        <TableRowColumn>{tag.value}</TableRowColumn>
                      </TableRow>
                     );
                  })}
              </TableBody>
            </Table>
          </CardText>
        </Card>
      </div>
    );
  }
}


class PointDialogComponent extends React.Component {

  handleClose = () => {
    this.props.onClosePointsClick();
  }

  render = () => {
    const actions = [
      <FlatButton
        label="Close"
        primary={true}
        onTouchTap={this.handleClose}
      />,
    ];

    let points = [];
    if( ! this.props.data.loading ) {
      points = this.props.data.viewer.sites[0].points;
    }

    return(
      <Dialog
        title="Haystack Points"
        modal={true}
        actions={actions}
        open={this.props.open}
        onRequestClose={this.handleClose}
      >
        <div className={styles.pointsRoot}>
          {
            points.map((point,i) => {
              return (<Point key={i} name={i} point={point}/>);
            })
          }
        </div>
      </Dialog>
    )
  }
}

const pointsQL = gql`
  query PointsQuery($siteRef: String!) {
    viewer {
      sites(siteRef: $siteRef) {
        points {
          dis
          tags {
            key
            value
          }
        }
      }
    }
  }
`;

const PointDialog = graphql(pointsQL, {
  options: (props) => ({
    pollInterval: 3000,
    variables: {
      siteRef: props.siteRef
    }
  })
})(PointDialogComponent);

class Sites extends React.Component {

  state = {
    selected: [],
    showPoints: false,
    disabled: true,
    showPointsSiteRef: null
  };

  isSelected = (index) => {
    return this.state.selected.indexOf(index) !== -1;
  };

  handleRowSelection = (selectedRows) => {
    this.setState({
      selected: selectedRows,
      disabled: (selectedRows.length == 0)
    });
  };

  onStartSimClick = () => {
    if (this.state.selected.length > 0) {
      this.props.startSimProp(this.props.data.viewer.sites[this.state.selected[0]].siteRef);
    }
  }

  onShowPointsClick = () => {
    this.setState({showPoints: true, showPointsSiteRef: this.props.data.viewer.sites[this.state.selected[0]].siteRef});
  }

  onClosePointsClick = () => {
    this.setState({showPoints: false, showPointsSiteRef: null});
  }

  conditionalDialog = () => {
    if( this.state.showPoints ) {
      return (<PointDialog open={this.state.showPoints} onClosePointsClick={this.onClosePointsClick} siteRef={this.state.showPointsSiteRef}></PointDialog>);
    } else {
      return null;
    }
  }

  render = () => {
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
                  <TableRow key={site.siteRef} selected={this.isSelected(i)}>
                    <TableRowColumn>{site.name}</TableRowColumn>
                    <TableRowColumn>{site.siteRef}</TableRowColumn>
                    <TableRowColumn>{site.simStatus}</TableRowColumn>
                  </TableRow>
                 );
              })}
            </TableBody>
            <TableFooter>
              <TableRow>
                <TableRowColumn>
                  <RaisedButton disabled={this.state.disabled} label='Start Simulation' onTouchTap={this.onStartSimClick}></RaisedButton>
                  <RaisedButton disabled={this.state.disabled} label='Show Points' onTouchTap={this.onShowPointsClick}></RaisedButton>
                </TableRowColumn>
              </TableRow>
            </TableFooter>
          </Table>
          {this.conditionalDialog()} 
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
      sites {
        name,
        siteRef,
        simStatus
      }
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

