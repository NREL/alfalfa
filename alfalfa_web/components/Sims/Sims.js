import { gql } from "@apollo/client";
import { graphql } from "@apollo/client/react/hoc";
import { MoreVert } from "@mui/icons-material";
import {
  Button,
  Checkbox,
  Dialog,
  DialogContent,
  DialogTitle,
  Grid,
  IconButton,
  List,
  ListItem,
  ListItemText,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow
} from "@mui/material";
import { withStyles } from "@mui/styles";
import downloadjs from "downloadjs";
import { DateTime } from "luxon";
import React from "react";

class ResultsDialog extends React.Component {
  render = () => {
    const { sim } = this.props;

    const items = (content) => {
      if (!content) {
        return <></>;
      }
      return Object.entries(content).map(([key, value]) => {
        if (key === "energy") {
          key += " [kWh]";
        } else if (key === "comfort") {
          key += " [K-h]";
        }
        return (
          <ListItem>
            <ListItemText primary={key} secondary={value.toFixed(3)} />
          </ListItem>
        );
      });
    };

    if (sim) {
      const content = JSON.parse(sim.results);
      return (
        <Dialog open={true} onBackdropClick={this.props.onBackdropClick}>
          <DialogTitle>{`Results for "${sim.name}"`}</DialogTitle>
          <DialogContent>
            <List>{items(content)}</List>
          </DialogContent>
        </Dialog>
      );
    } else {
      return null;
    }
  };
}

class Sims extends React.Component {
  state = {
    selected: []
  };

  isSelected = (simRef) => {
    return this.state.selected.indexOf(simRef) !== -1;
  };

  selectedSims = () => {
    return this.props.data.viewer.sims.filter((sim) => {
      return this.state.selected.some((simRef) => {
        return simRef === sim.simRef;
      });
    });
  };

  handleRowClick = (event, simRef) => {
    const { selected } = this.state;
    const selectedIndex = selected.indexOf(simRef);
    let newSelected = [];

    if (selectedIndex === -1) {
      newSelected = newSelected.concat(selected, simRef);
    } else if (selectedIndex === 0) {
      newSelected = newSelected.concat(selected.slice(1));
    } else if (selectedIndex === selected.length - 1) {
      newSelected = newSelected.concat(selected.slice(0, -1));
    } else if (selectedIndex > 0) {
      newSelected = newSelected.concat(selected.slice(0, selectedIndex), selected.slice(selectedIndex + 1));
    }

    this.setState({ selected: newSelected });
  };

  buttonsDisabled = () => {
    return this.state.selected.length === 0;
  };

  handleRemove = () => {
    console.log("Handle Remove");
  };

  handleDownload = () => {
    this.selectedSims().map((sim) => {
      let url = new URL(sim.url);
      let local_s3 = true;
      if (local_s3) {
        url.hostname = window.location.hostname;
        url.pathname = "/alfalfa" + url.pathname;
      }
      const xhr = new XMLHttpRequest();
      xhr.open("GET", url, true);
      xhr.responseType = "blob";
      xhr.onload = (e) => {
        downloadjs(e.target.response, sim.name + ".tar.gz");
      };
      xhr.send();
    });
  };

  handleShowResults = (e, sim) => {
    this.setState({ showResults: sim });
    e.stopPropagation();
  };

  handleCloseResults = (e, sim) => {
    this.setState({ showResults: null });
    e.stopPropagation();
  };

  render = () => {
    const { classes } = this.props;

    if (this.props.data.loading) {
      return null;
    } else {
      const sims = this.props.data.viewer.sims;
      const buttonsDisabled = this.buttonsDisabled();
      return (
        <Grid container direction="column">
          <ResultsDialog sim={this.state.showResults} onBackdropClick={this.handleCloseResults} />
          <Grid item>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell padding="checkbox"></TableCell>
                  <TableCell>Name</TableCell>
                  <TableCell>Completed Time</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>KPIs</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {sims.map((sim) => {
                  const isSelected = this.isSelected(sim.simRef);
                  return (
                    <TableRow
                      key={sim.simRef}
                      style={{ cursor: "default" }}
                      onClick={(event) => this.handleRowClick(event, sim.simRef)}>
                      <TableCell padding="checkbox">
                        <Checkbox checked={isSelected} />
                      </TableCell>
                      <TableCell padding="none">{sim.name}</TableCell>
                      <TableCell>
                        {DateTime.fromISO(sim.timeCompleted.replace(" ", "T")).toFormat("LLLL dd y, h:mm a")}
                      </TableCell>
                      <TableCell padding="none">{sim.simStatus}</TableCell>
                      <TableCell>
                        <IconButton onClick={(event) => this.handleShowResults(event, sim)}>
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
                <Button className={classes.button} variant="contained" disabled={true} onClick={this.handleRemove}>
                  Remove Test Results
                </Button>
              </Grid>
              <Grid item>
                <Button
                  className={classes.button}
                  variant="contained"
                  disabled={buttonsDisabled}
                  onClick={this.handleDownload}>
                  Download Test Results
                </Button>
              </Grid>
            </Grid>
          </Grid>
        </Grid>
      );
    }
  };
}

const simsQL = gql`
  query SimsQuery {
    viewer {
      sims {
        simRef
        name
        simStatus
        siteRef
        url
        timeCompleted
        results
      }
    }
  }
`;

const withSims = graphql(simsQL, {
  options: {
    pollInterval: 1000
  }
})(Sims);

const styles = (theme) => ({
  controls: {
    marginLeft: 16
  },
  button: {
    margin: `${theme.spacing(1)}!important`
  }
});

const withStyle = withStyles(styles)(withSims);

export default withStyle;
