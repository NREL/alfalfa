/***********************************************************************************************************************
*  Copyright (c) 2008-2018, Alliance for Sustainable Energy, LLC, and other contributors. All rights reserved.
*
*  Redistribution and use in source and binary forms, with or without modification, are permitted provided that the
*  following conditions are met:
*
*  (1) Redistributions of source code must retain the above copyright notice, this list of conditions and the following
*  disclaimer.
*
*  (2) Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following
*  disclaimer in the documentation and/or other materials provided with the distribution.
*
*  (3) Neither the name of the copyright holder nor the names of any contributors may be used to endorse or promote products
*  derived from this software without specific prior written permission from the respective party.
*
*  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDER(S) AND ANY CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
*  INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
*  DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER(S), ANY CONTRIBUTORS, THE UNITED STATES GOVERNMENT, OR THE UNITED
*  STATES DEPARTMENT OF ENERGY, NOR ANY OF THEIR EMPLOYEES, BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
*  EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
*  USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
*  STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
*  ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
***********************************************************************************************************************/

import React, { PropTypes } from 'react';
import {FileUpload, MoreVert, ExpandLess, ExpandMore} from '@material-ui/icons';
import TextField from '@material-ui/core/TextField';
import Button from '@material-ui/core/Button';
import IconButton from '@material-ui/core/IconButton';
import Typography from '@material-ui/core/Typography';
import Dialog, {
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
} from '@material-ui/core/Dialog';
import ExpansionPanel, {
  ExpansionPanelDetails,
  ExpansionPanelSummary,
} from '@material-ui/core/ExpansionPanel';
import Grid from '@material-ui/core/Grid';
import Card, {CardActions, CardHeader, CardText} from '@material-ui/core/Card';
import List, { ListItem, ListItemIcon, ListItemText } from '@material-ui/core/List';
import {cyan500, red500, greenA200} from '@material-ui/core/colors';
import { graphql } from 'react-apollo';
import gql from 'graphql-tag';
import Table from '@material-ui/core/Table';
import TableBody from '@material-ui/core/TableBody';
import TableCell from '@material-ui/core/TableCell';
import TableHead from '@material-ui/core/TableHead';
import TableRow from '@material-ui/core/TableRow';
import CircularProgress from '@material-ui/core/CircularProgress';
import Checkbox from '@material-ui/core/Checkbox';
import { withStyles } from '@material-ui/core/styles';
import StartDialog from '../StartDialog/StartDialog.js';

class PointDialogComponent extends React.Component {

  //handleRequestClose = () => {
  //  this.props.onClosePointsClick();
  //}

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
      return (
        <Grid container justify="center" alignItems="center">
          <Grid item><CircularProgress/></Grid>
        </Grid>
      );
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
    if( this.props.site ) {
      return(
        <div>
          <Dialog open={true} onBackdropClick={this.props.onBackdropClick}>
            <DialogTitle>{this.props.site.name + ' Points'}</DialogTitle>
            <DialogContent>
              {this.table()}
            </DialogContent>
          </Dialog>
        </div>
      )
    } else {
      return (<div></div>);
    }
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
  options: (props) => {
    let siteRef = "";
    if( props.site ) {
      siteRef = props.site.siteRef;
    }
    return ({
      pollInterval: 1000,
      variables: {
        siteRef
      }
    })
  }
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

  showSiteRef = () => {
    if( this.state.showSite ) {
      return this.state.showSite.siteRef;
    } else {
      return "";
    }
  }

  render = (props) => {
    const { classes } = this.props;

    if( ! this.props.data.loading ) {
      const isStartDisabled = this.isStartButtonDisabled();
      const isStopDisabled = this.isStopButtonDisabled();
      const isRemoveDisabled = this.isRemoveButtonDisabled();

      return (
        <Grid container direction="column">
          <PointDialog site={this.state.showSite} onBackdropClick={this.handleRequestClosePoints} />
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
                <StartDialog disabled={isStartDisabled} onStartSimulation={this.handleStartSimulation}></StartDialog>
              </Grid>
              <Grid item>
                <Button variant="contained" className={classes.button} disabled={isStopDisabled} onClick={this.handleStopSimulation}>Stop Simulation</Button>
              </Grid>
              <Grid item>
                <Button variant="contained" className={classes.button} disabled={isRemoveDisabled} onClick={this.handleRemoveSite}>Remove Site</Button>
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
  button: {
    margin: theme.spacing.unit,
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
const runSiteQL = gql`
  mutation runSiteMutation($siteRef: String!, $startDatetime: String, $endDatetime: String, $timescale: Float, $realtime: String ) {
    runSite(siteRef: $siteRef, startDatetime: $startDatetime, endDatetime: $endDatetime, timescale: $timescale, realtime: $realtime)
  }
`;

const stopSiteQL = gql`
  mutation stopSiteMutation($siteRef: String!) {
    stopSite(siteRef: $siteRef)
  }
`;

const removeSiteQL = gql`
  mutation removeSiteMutation($siteRef: String!) {
    removeSite(siteRef: $siteRef)
  }
`;

const withStyle = withStyles(styles)(Sites);

const withStart = graphql(runSiteQL, {
  props: ({ mutate }) => ({
    startSimProp: (siteRef, startDatetime, endDatetime, timescale, realtime) => mutate({ variables: { siteRef, startDatetime, endDatetime, timescale, realtime } }),
  })
})(withStyle);

const withStop = graphql(stopSiteQL, {
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

