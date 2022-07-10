import { gql } from "@apollo/client";
import { graphql } from "@apollo/client/react/hoc";
import { MoreVert } from "@mui/icons-material";
import { Button, Checkbox, Grid, IconButton, Table, TableBody, TableCell, TableHead, TableRow } from "@mui/material";
import { withStyles } from "@mui/styles";
import React from "react";
import StartDialog from "../StartDialog/StartDialog";
import PointDialogComponent from "./PointDialogComponent";

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
    if (props.site) {
      siteRef = props.site.siteRef;
    }
    return {
      pollInterval: 1000,
      variables: {
        siteRef
      }
    };
  }
})(PointDialogComponent);

class Sites extends React.Component {
  state = {
    selected: [],
    disabled: true,
    showPointsSiteRef: null,
    startDialogType: "osm"
  };

  isSelected = (siteRef) => {
    return this.state.selected.indexOf(siteRef) !== -1;
  };

  handleRowClick = (event, siteRef) => {
    const { selected } = this.state;
    const selectedIndex = selected.indexOf(siteRef);
    let newSelected = [];

    // Don't let two different simulation types be selected
    const firstSimType = "osm";

    const clickedSite = this.props.data.viewer.sites.find((s) => s.siteRef === siteRef);
    const firstSite = this.selectedSites()[0];
    const simType = clickedSite.simType;
    if (firstSite && simType !== firstSite.simType) {
      return;
    }

    if (selectedIndex === -1) {
      newSelected = newSelected.concat(selected, siteRef);
    } else if (selectedIndex === 0) {
      newSelected = newSelected.concat(selected.slice(1));
    } else if (selectedIndex === selected.length - 1) {
      newSelected = newSelected.concat(selected.slice(0, -1));
    } else if (selectedIndex > 0) {
      newSelected = newSelected.concat(selected.slice(0, selectedIndex), selected.slice(selectedIndex + 1));
    }

    this.setState({ selected: newSelected, startDialogType: simType });
  };

  isStartButtonDisabled = () => {
    const readyItem = this.selectedSites().some((item) => item.simStatus === "READY");

    return !readyItem;
  };

  isStopButtonDisabled = () => {
    const runningItem = this.selectedSites().some((item) => {
      return ["RUNNING", "PREPROCESSING", "STARTING", "STARTED", "STOPPING"].includes(item.simStatus);
    });

    return !runningItem;
  };

  isRemoveButtonDisabled = () => {
    const stoppedItem = this.selectedSites().some((item) => {
      return ["READY", "COMPLETE", "ERROR"].includes(item.simStatus);
    });

    return !stoppedItem;
  };

  handleStartSimulation = (startDatetime, endDatetime, timescale, realtime, externalClock) => {
    this.selectedSites().map((item) => {
      this.props.startSimProp(item.siteRef, startDatetime, endDatetime, timescale, realtime, externalClock);
    });
  };

  handleStopSimulation = () => {
    this.selectedSites().map((item) => {
      this.props.stopSimProp(item.siteRef);
    });
  };

  handleRemoveSite = () => {
    this.selectedSites().map((item) => {
      this.props.removeSiteProp(item.siteRef);
    });
  };

  selectedSites = () => {
    return this.props.data.viewer.sites.filter((site) => {
      return this.state.selected.some((siteRef) => siteRef === site.siteRef);
    });
  };

  handleRequestShowPoints = (e, site) => {
    this.setState({ showSite: site });
    e.stopPropagation();
  };

  handleRequestClosePoints = () => {
    this.setState({ showSite: null });
  };

  render = () => {
    const { classes } = this.props;

    if (this.props.data.loading) {
      return null;
    } else {
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
                  <TableCell padding="checkbox" />
                  <TableCell>Name</TableCell>
                  <TableCell>ID</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Time</TableCell>
                  <TableCell />
                </TableRow>
              </TableHead>
              <TableBody>
                {this.props.data.viewer.sites.map((site, i) => {
                  const isSelected = this.isSelected(site.siteRef);
                  return (
                    <TableRow
                      key={site.siteRef}
                      selected={false}
                      style={{ cursor: "default" }}
                      onClick={(event) => this.handleRowClick(event, site.siteRef)}>
                      <TableCell padding="checkbox">
                        <Checkbox checked={isSelected} />
                      </TableCell>
                      <TableCell padding="none">{site.name}</TableCell>
                      <TableCell>{site.siteRef}</TableCell>
                      <TableCell>{site.simStatus}</TableCell>
                      <TableCell>{site.datetime}</TableCell>
                      <TableCell>
                        <IconButton onClick={(event) => this.handleRequestShowPoints(event, site)}>
                          <MoreVert />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </Grid>
          <Grid item>
            <Grid
              className={classes.controls}
              container
              justifyContent="flex-start"
              alignItems="center"
              style={{ marginLeft: 0, paddingLeft: 16 }}>
              <Grid item>
                <StartDialog
                  type={this.state.startDialogType}
                  disabled={isStartDisabled}
                  onStartSimulation={this.handleStartSimulation}
                />
              </Grid>
              <Grid item>
                <Button
                  variant="contained"
                  className={classes.button}
                  disabled={isStopDisabled}
                  onClick={this.handleStopSimulation}>
                  Stop Test
                </Button>
              </Grid>
              <Grid item>
                <Button
                  variant="contained"
                  className={classes.button}
                  disabled={isRemoveDisabled}
                  onClick={this.handleRemoveSite}>
                  Remove Test Case
                </Button>
              </Grid>
            </Grid>
          </Grid>
        </Grid>
      );
    }
  };
}

const styles = (theme) => ({
  controls: {
    marginLeft: 16
  },
  button: {
    margin: `${theme.spacing(1)}!important`
  }
});

const sitesQL = gql`
  query QueueQuery {
    viewer {
      sites {
        name
        datetime
        siteRef
        simStatus
        simType
        step
      }
    }
  }
`;

// TODO: make an input type
const runSiteQL = gql`
  mutation runSiteMutation(
    $siteRef: String!
    $startDatetime: String
    $endDatetime: String
    $timescale: Float
    $realtime: Boolean
    $externalClock: Boolean
  ) {
    runSite(
      siteRef: $siteRef
      startDatetime: $startDatetime
      endDatetime: $endDatetime
      timescale: $timescale
      realtime: $realtime
      externalClock: $externalClock
    )
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
    startSimProp: (siteRef, startDatetime, endDatetime, timescale, realtime, externalClock) =>
      mutate({ variables: { siteRef, startDatetime, endDatetime, timescale, realtime, externalClock } })
  })
})(withStyle);

const withStop = graphql(stopSiteQL, {
  props: ({ mutate }) => ({
    stopSimProp: (siteRef) => mutate({ variables: { siteRef } })
  })
})(withStart);

const withRemove = graphql(removeSiteQL, {
  props: ({ mutate }) => ({
    removeSiteProp: (siteRef) => mutate({ variables: { siteRef } })
  })
})(withStop);

const withSites = graphql(sitesQL, {
  options: {
    pollInterval: 1000
  }
})(withRemove);

export default withSites;
