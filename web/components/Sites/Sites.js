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
import DatePicker from 'material-ui/DatePicker';
import TimePicker from 'material-ui/TimePicker';
import MoreHorizIcon from 'material-ui/svg-icons/navigation/more-horiz';
import CircularProgress from 'material-ui/CircularProgress';

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

class StartDialog extends React.Component {
  state = {
    open: false,
  }

  onShowDialogClick = () => {
    this.setState({open: true});
  }

  onCancel = () => {
    this.setState({open: false});
  }

  onBegin = () => {
    this.setState({open: false});
  }

  render = () => {
    const actions = [
      <FlatButton
        label="Cancel"
        primary={false}
        onClick={this.onCancel}
      />,
      <FlatButton
        label="Start"
        primary={true}
        onClick={this.onBegin}
      />,
    ];

    return (
      <div>
        <RaisedButton disabled={this.props.disabled} label='Start Simulation' onTouchTap={this.onShowDialogClick}></RaisedButton>
        <Dialog open={this.state.open} actions={actions} >
          <DatePicker hintText="Select Start Date" container="inline" mode="landscape" />
          <TimePicker hintText="Select Start Time" />
          <DatePicker hintText="Select End Date" container="inline" mode="landscape" />
          <TimePicker hintText="Select End Time" />
        </Dialog>
      </div>
    );
  }
};


class PointDialogComponent extends React.Component {

  handleClose = () => {
    this.props.onClosePointsClick();
  }

  table = () => {
    if( ! this.props.data.loading ) {
      let points = this.props.data.viewer.sites[0].points;
      return(
      <div className={styles.pointsRoot}>
        {
          points.map((point,i) => {
            return (<Point key={i} name={i} point={point}/>);
          })
        }
      </div>
      );
    } else {
      return (<div className={styles.centerLoading}><CircularProgress/></div>);
    }
  }

  render = () => {
    const actions = [
      <FlatButton
        label="Close"
        primary={true}
        onTouchTap={this.handleClose}
      />,
    ];


    return(
      <Dialog
        title="Haystack Points"
        modal={true}
        actions={actions}
        open={this.props.open}
        onRequestClose={this.handleClose}
      >
      {this.table()}
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
    pollInterval: 1000,
    variables: {
      siteRef: props.siteRef
    }
  })
})(PointDialogComponent);

class Sites extends React.Component {

  state = {
    selected: [],
    disabled: true,
    showPointsSiteRef: null,
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

  onShowPointsClick = (siteRef) => {
    this.setState({showPointsSiteRef: siteRef});
  }

  onClosePointsClick = () => {
    this.setState({showPointsSiteRef: null});
  }

  conditionalPointDialog = () => {
    if( this.state.showPointsSiteRef != null ) {
      return (<PointDialog open={true} onClosePointsClick={this.onClosePointsClick} siteRef={this.state.showPointsSiteRef}></PointDialog>);
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
                <TableHeaderColumn></TableHeaderColumn>
              </TableRow>
            </TableHeader>
            <TableBody deselectOnClickaway={false}>
              {this.props.data.viewer.sites.map((site, i) => {
                 return (
                  <TableRow key={site.siteRef} selected={this.isSelected(i)}>
                    <TableRowColumn>{site.name}</TableRowColumn>
                    <TableRowColumn>{site.siteRef}</TableRowColumn>
                    <TableRowColumn>{site.simStatus}</TableRowColumn>
                    <TableRowColumn><IconButton onTouchTap={() => { this.onShowPointsClick(site.siteRef) }}><MoreHorizIcon></MoreHorizIcon></IconButton></TableRowColumn>
                  </TableRow>
                 );
              })}
            </TableBody>
            <TableFooter>
              <TableRow>
                <TableRowColumn>
                  <StartDialog disabled={this.state.disabled} label='Start Simulation'></StartDialog>
                </TableRowColumn>
              </TableRow>
            </TableFooter>
          </Table>
          {this.conditionalPointDialog()} 
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

