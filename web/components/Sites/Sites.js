import React, { PropTypes } from 'react';
import {FileUpload, MoreVert, ExpandLess, ExpandMore} from 'material-ui-icons';
import TextField from 'material-ui/TextField';
import Button from 'material-ui/Button';
import IconButton from 'material-ui/IconButton';
import Typography from 'material-ui/Typography';
import Dialog, {
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
} from 'material-ui/Dialog';
import ExpansionPanel, {
  ExpansionPanelDetails,
  ExpansionPanelSummary,
} from 'material-ui/ExpansionPanel';
import Card, {CardActions, CardHeader, CardText} from 'material-ui/Card';
import List, { ListItem, ListItemIcon, ListItemText } from 'material-ui/List';
import {cyan500, red500, greenA200} from 'material-ui/colors';
import { graphql } from 'react-apollo';
import gql from 'graphql-tag';
import Table, {TableBody, TableHead, TableFooter, TableCell, TableRow} from 'material-ui/Table';
import {CircularProgress} from 'material-ui/Progress';
import Checkbox from 'material-ui/Checkbox';
import Collapse from 'material-ui/transitions/Collapse';
import { withStyles } from 'material-ui/styles';
import StartDialog from '../StartDialog/StartDialog.js';

class PointDialogComponent extends React.Component {

  handleRequestClose = () => {
    this.props.onClosePointsClick();
  }

  state = {
    expanded: null,
  };

  handleChange = pointId => (event, expanded) => {
    this.setState({
      expanded: expanded ? pointId : false,
    });
  };

  table = () => {
    if( this.props.data.loading ) {
      return (<div><CircularProgress/></div>);
    } else {
      const points = this.props.data.viewer.sites[0].points;
      const { expanded } = this.state;
      return(
      <div>
        {
          points.map((point,i) => {
            return (
              <ExpansionPanel key={i} expanded={expanded === i} onChange={this.handleChange(i)}>
                <ExpansionPanelSummary expandIcon={<ExpandMore />}>
                  <Typography>{point.dis}</Typography>
                </ExpansionPanelSummary>
                <ExpansionPanelDetails>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Key</TableCell>
                        <TableCell>Value</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                        {point.tags.map((tag) => {
                           return (
                            <TableRow key={tag.key}>
                              <TableCell>{tag.key}</TableCell>
                              <TableCell>{tag.value}</TableCell>
                            </TableRow>
                           );
                        })}
                    </TableBody>
                  </Table>
                </ExpansionPanelDetails>
              </ExpansionPanel>
            )
          })
        }
      </div>
      );
    }
  }

  render = () => {
    return(
      <div>
        <Dialog open={true} onRequestClose={this.handleRequestClose}>
          <DialogTitle>{this.props.site.name + ' Points'}</DialogTitle>
          <DialogContent>
            {this.table()}
          </DialogContent>
        </Dialog>
      </div>
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
      siteRef: props.site.siteRef
    }
  })
})(PointDialogComponent);

class Sites extends React.Component {

  state = {
    selected: [],
    disabled: true,
    showPointsSiteRef: null,
  };

  isSelected = (siteRef) => {
    return this.state.selected.indexOf(siteRef) !== -1;
  };

  handleRowClick = (event, siteRef) => {
    const { selected } = this.state;
    const selectedIndex = selected.indexOf(siteRef);
    let newSelected = [];

    if (selectedIndex === -1) {
      newSelected = newSelected.concat(selected, siteRef);
    } else if (selectedIndex === 0) {
      newSelected = newSelected.concat(selected.slice(1));
    } else if (selectedIndex === selected.length - 1) {
      newSelected = newSelected.concat(selected.slice(0, -1));
    } else if (selectedIndex > 0) {
      newSelected = newSelected.concat(
        selected.slice(0, selectedIndex),
        selected.slice(selectedIndex + 1),
      );
    }

    this.setState({ selected: newSelected });
  };

  handleStartSimulation = () => {
    if (this.state.selected.length > 0) {
      this.props.startSimProp(this.state.selected[0]);
    }
  }

  handleRequestShowPoints = (e, site) => {
    this.setState({ showSite: site });
    e.stopPropagation();
  }

  handleRequestClosePoints = () => {
    this.setState({ showSite: null });
  }

  conditionalPointDialog = () => {
    if( this.state.showSite != null ) {
      return (<PointDialog onClosePointsClick={this.handleRequestClosePoints} site={this.state.showSite}></PointDialog>);
    } else {
      return null;
    }
  }

  formatTime = (isotime) => {
    let result = "-";

    if( isotime ) {
      // Haystack has an extra string representation of the timezone
      // tacked onto the end of the iso time string (after a single space)
      // Here we remove that extra timezone designation
      const _isotime = isotime.replace(/\s[\w]*/,'');
      // Use these options do show year and day of week
      //const options = {  
      //    weekday: "long", year: "numeric", month: "short",  
      //    day: "numeric", hour: "2-digit", minute: "2-digit"  
      //};  
      // For now keep it simple
      const options = {  
          month: "short",  
          day: "numeric", hour: "2-digit", minute: "2-digit"  
      };  
      const datetime = new Date(_isotime);
      result = datetime.toLocaleTimeString("en-us", options);
    }

    return result;
  }

  render = () => {
    if( ! this.props.data.loading ) {
      return (
        <div>
          {this.conditionalPointDialog()}
          <Table>
            <TableHead>
              <TableRow>
                <TableCell padding="checkbox"></TableCell>
                <TableCell>Name</TableCell>
                <TableCell>Site Reference</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Time</TableCell>
                <TableCell></TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {this.props.data.viewer.sites.map((site, i) => {
                 const isSelected = this.isSelected(site.siteRef);
                 return (
                  <TableRow key={site.siteRef} 
                    selected={this.isSelected(i)}
                    onClick={event => this.handleRowClick(event, site.siteRef)} 
                  >
                    <TableCell padding="checkbox">
                      <Checkbox
                        checked={isSelected}
                      />
                    </TableCell>
                    <TableCell padding="none">{site.name}</TableCell>
                    <TableCell>{site.siteRef}</TableCell>
                    <TableCell>{site.simStatus}</TableCell>
                    <TableCell>{this.formatTime(site.datetime)}</TableCell>
                    <TableCell><IconButton onClick={event => this.handleRequestShowPoints(event, site)}><MoreVert/></IconButton></TableCell>
                  </TableRow>
                 );
              })}
            </TableBody>
            <TableFooter>
              <TableRow>
                <TableCell>
                  <StartDialog disabled={this.state.selected.length == 0} onStartSimulation={this.handleStartSimulation}></StartDialog>
                </TableCell>
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
      sites {
        name,
        datetime,
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

