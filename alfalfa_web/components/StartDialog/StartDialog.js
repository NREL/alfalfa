import { DateTimePicker } from "@mui/x-date-pickers";
import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControlLabel,
  Grid,
  Switch,
  TextField
} from "@mui/material";
import { withStyles } from "@mui/styles";
import { DateTime } from "luxon";
import React from "react";

const styles = (theme) => ({
  label: {
    whiteSpace: "nowrap"
  },
  button: {
    margin: `${theme.spacing(1)}!important`
  }
});

const timeFormat = "y-LL-dd HH:mm:ss";

class StartDialog extends React.Component {
  constructor(props) {
    super(props);

    this.state = {
      open: false,
      realtime: false,
      externalClock: false,
      timescale: 5,
      selectedStartTime: "",
      selectedEndTime: "",
      selectedStartSeconds: 0,
      selectedEndSeconds: 86400
    };

    if (this.props.type === "osm") {
      const time = DateTime.now().toFormat(timeFormat);
      this.state.selectedStartTime = time;
      this.state.selectedEndTime = time;
    }
  }

  handleStartTimeChange = (time) => {
    this.setState({ selectedStartTime: time.toFormat(timeFormat) });
  };

  handleTimescaleChange = (event) => {
    this.setState({ timescale: Number(event.target.value) });
  };

  handleEndTimeChange = (time) => {
    this.setState({ selectedEndTime: time.toFormat(timeFormat) });
  };

  handleStartSecondChange = (event) => {
    this.setState({ selectedStartSeconds: event.target.value });
  };

  handleEndSecondChange = (event) => {
    this.setState({ selectedEndSeconds: event.target.value });
  };

  handleShowDialogClick = () => {
    this.setState({ open: true });
  };

  handleRequestClose = () => {
    this.setState({ open: false });
  };

  handleRequestStart = () => {
    if (this.props.type === "osm") {
      this.props.onStartSimulation(
        this.state.selectedStartTime,
        this.state.selectedEndTime,
        this.state.timescale,
        this.state.realtime,
        this.state.externalClock
      );
      this.setState({ open: false });
    } else {
      this.props.onStartSimulation(
        this.state.selectedStartSeconds.toString(),
        this.state.selectedEndSeconds.toString(),
        this.state.timescale,
        this.state.realtime,
        this.state.externalClock
      );
      this.setState({ open: false });
    }
  };

  render = () => {
    const {
      externalClock,
      open,
      realtime,
      selectedEndSeconds,
      selectedEndTime,
      selectedStartSeconds,
      selectedStartTime,
      timescale
    } = this.state;
    const { classes, disabled, type } = this.props;

    let start;
    let stop;
    if (type === "osm") {
      start = (
        <Grid item xs={6}>
          <DateTimePicker
            value={selectedStartTime}
            onChange={this.handleStartTimeChange}
            label="EnergyPlus Start Time"
            disabled={realtime || externalClock}
            renderInput={(params) => <TextField {...params} />}
          />
        </Grid>
      );

      stop = (
        <Grid item xs={6}>
          <DateTimePicker
            value={selectedEndTime}
            onChange={this.handleEndTimeChange}
            label="EnergyPlus End Time"
            disabled={realtime || externalClock}
            renderInput={(params) => <TextField {...params} />}
          />
        </Grid>
      );
    } else {
      start = (
        <Grid item xs={6}>
          <TextField
            label="FMU Start Time"
            value={selectedStartSeconds}
            onChange={this.handleStartSecondChange}
            InputLabelProps={{ shrink: true, className: classes.label }}
            disabled={realtime || externalClock}
            inputProps={{ type: "number", max: selectedEndSeconds }}
          />
        </Grid>
      );

      stop = (
        <Grid item xs={6}>
          <TextField
            label="FMU Stop Time"
            value={selectedEndSeconds}
            onChange={this.handleEndSecondChange}
            InputLabelProps={{ shrink: true, className: classes.label }}
            disabled={realtime || externalClock}
            inputProps={{ type: "number", min: selectedStartSeconds }}
          />
        </Grid>
      );
    }

    return (
      <div>
        <Button className={classes.button} variant="contained" disabled={disabled} onClick={this.handleShowDialogClick}>
          Start Test
        </Button>
        <Dialog fullWidth={true} maxWidth="sm" open={open}>
          <DialogTitle>Simulation Parameters</DialogTitle>
          <DialogContent>
            <Grid container spacing={2} style={{ paddingTop: 8 }}>
              {start}
              {stop}
              <Grid item xs={12}>
                <TextField
                  label="Timescale"
                  value={timescale}
                  onChange={this.handleTimescaleChange}
                  InputLabelProps={{ shrink: true, className: classes.label }}
                  disabled={realtime || externalClock}
                  inputProps={{ type: "number", min: 1, max: 200 }}
                />
              </Grid>
              <Grid item xs={6}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={realtime}
                      disabled={externalClock}
                      onChange={(event, checked) => this.setState({ realtime: checked })}
                    />
                  }
                  label="Realtime Simulation"
                />
              </Grid>
              <Grid item xs={6}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={externalClock}
                      disabled={realtime}
                      onChange={(event, checked) => this.setState({ externalClock: checked })}
                    />
                  }
                  label="External Clock"
                />
              </Grid>
            </Grid>
          </DialogContent>
          <DialogActions>
            <Button onClick={this.handleRequestClose} color="primary">
              Cancel
            </Button>
            <Button onClick={this.handleRequestStart} color="primary">
              Run
            </Button>
          </DialogActions>
        </Dialog>
      </div>
    );
  };
}

export default withStyles(styles)(StartDialog);
