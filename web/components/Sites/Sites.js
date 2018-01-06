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
import Grid from 'material-ui/Grid';
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

  isStartButtonDisabled = () => {
    const stoppedItem = this.selectedSites().some((item) => {
      return (item.simStatus === "Stopped");
    });

    return (! stoppedItem)
  }

  isStopButtonDisabled = () => {
    const runningItem = this.selectedSites().some((item) => {
      return (item.simStatus === "Running");
    });

    return (! runningItem);
  }

  isRemoveButtonDisabled = () => {
    const stoppedItem = this.selectedSites().some((item) => {
      return (item.simStatus === "Stopped");
    });

    return (! stoppedItem);
  }

  handleStartSimulation = (startDatetime,endDatetime,timescale,realtime) => {
    this.selectedSites().map((item) => {
      this.props.startSimProp(item.siteRef,startDatetime,endDatetime,timescale,realtime);
    })
  }

  handleStopSimulation = () => {
    this.selectedSites().map((item) => {
      this.props.stopSimProp(item.siteRef);
    })
  }

  handleRemoveSite = () => {
    this.selectedSites().map((item) => {
      this.props.removeSiteProp(item.siteRef);
    })
  }

  selectedSites = () => {
    return this.props.data.viewer.sites.filter((site) => {
      return this.state.selected.some((siteRef) => {
        return (siteRef === site.siteRef);
      })
    });
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

  render = (props) => {
    const { classes } = this.props;

    if( ! this.props.data.loading ) {
      return (
        <Grid container direction="column">
          {this.conditionalPointDialog()}
          <Grid item>
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
                      selected={false}
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
            </Table>
          </Grid>
          <Grid item>
            <Grid className={classes.controls} container justify="flex-start" alignItems="center" >
              <Grid item>
                <StartDialog disabled={this.isStartButtonDisabled()} onStartSimulation={this.handleStartSimulation}></StartDialog>
              </Grid>
              <Grid item>
                <Button raised disabled={this.isStopButtonDisabled()} onTouchTap={this.handleStopSimulation}>Stop Simulation</Button>
              </Grid>
              <Grid item>
                <Button raised disabled={this.isRemoveButtonDisabled()} onTouchTap={this.handleRemoveSite}>Remove Site</Button>
              </Grid>
            </Grid>
          </Grid>
        </Grid>
      );
    } else {
      return null;
    }
  }
}

const styles = theme => ({
  controls: {
    marginLeft: 16,
  },
});

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

// TODO: make an input type
const startSimQL = gql`
  mutation startSimulationMutation($siteRef: String!, $startDatetime: String, $endDatetime: String, $timescale: Float, $realtime: String ) {
    startSimulation(siteRef: $siteRef, startDatetime: $startDatetime, endDatetime: $endDatetime, timescale: $timescale, realtime: $realtime)
  }
`;

const stopSimQL = gql`
  mutation stopSimulationMutation($siteRef: String!) {
    stopSimulation(siteRef: $siteRef)
  }
`;

const removeSiteQL = gql`
  mutation removeSiteMutation($siteRef: String!) {
    removeSite(siteRef: $siteRef)
  }
`;

const withStyle = withStyles(styles)(Sites);

const withStart = graphql(startSimQL, {
  props: ({ mutate }) => ({
    startSimProp: (siteRef, startDatetime, endDatetime, timescale, realtime) => mutate({ variables: { siteRef, startDatetime, endDatetime, timescale, realtime } }),
  })
})(withStyle);

const withStop = graphql(stopSimQL, {
  props: ({ mutate }) => ({
    stopSimProp: (siteRef) => mutate({ variables: { siteRef } }),
  })
})(withStart);

const withRemove = graphql(removeSiteQL, {
  props: ({ mutate }) => ({
    removeSiteProp: (siteRef) => mutate({ variables: { siteRef } }),
  })
})(withStop);

const withSites = graphql(sitesQL, {
  options: { 
    pollInterval: 1000,
  },
})(withRemove) 

export default withSites;

