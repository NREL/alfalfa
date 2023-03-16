import React, { useState } from "react";
import { Close } from "@mui/icons-material";
import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControlLabel,
  Grid,
  IconButton,
  Switch,
  TextField
} from "@mui/material";
import { DateTimePicker } from "@mui/x-date-pickers";
import { DateTime } from "luxon";

export const StartDialog = ({ onClose, onStartSimulation, type }) => {
  const timeFormat = "y-LL-dd HH:mm:ss";

  const currentTime = DateTime.now();
  const [realtime, setRealtime] = useState(false);
  const [externalClock, setExternalClock] = useState(false);
  const [timescale, setTimescale] = useState(5);
  const [selectedStartTime, setSelectedStartTime] = useState(currentTime);
  const [selectedEndTime, setSelectedEndTime] = useState(currentTime);
  const [selectedStartSeconds, setSelectedStartSeconds] = useState(0);
  const [selectedEndSeconds, setSelectedEndSeconds] = useState(86400);

  const handleTimescaleChange = (event) => {
    setTimescale(Number(event.target.value));
  };

  const handleStartSecondChange = (event) => {
    setSelectedStartSeconds(event.target.value);
  };

  const handleEndSecondChange = (event) => {
    setSelectedEndSeconds(event.target.value);
  };

  const handleRequestStart = () => {
    if (type === "osm") {
      onStartSimulation(
        selectedStartTime.toFormat(timeFormat),
        selectedEndTime.toFormat(timeFormat),
        timescale,
        realtime,
        externalClock
      );
    } else {
      onStartSimulation(
        selectedStartSeconds.toString(),
        selectedEndSeconds.toString(),
        timescale,
        realtime,
        externalClock
      );
    }
    onClose();
  };

  const runDisabled = () => {
    if (type === "osm") {
      return selectedEndTime < selectedStartTime;
    }
    return selectedEndSeconds < selectedStartSeconds;
  };

  let start;
  let stop;
  if (type === "osm") {
    start = (
      <Grid item xs={6}>
        <DateTimePicker
          label="EnergyPlus Start Time"
          format={timeFormat}
          value={selectedStartTime}
          onChange={setSelectedStartTime}
          slotProps={{ textField: { sx: { width: "100%" } } }}
        />
      </Grid>
    );

    stop = (
      <Grid item xs={6}>
        <DateTimePicker
          label="EnergyPlus End Time"
          format={timeFormat}
          value={selectedEndTime}
          onChange={setSelectedEndTime}
          slotProps={{ textField: { sx: { width: "100%" } } }}
        />
      </Grid>
    );
  } else {
    start = (
      <Grid item xs={6}>
        <TextField
          label="FMU Start Time"
          value={selectedStartSeconds}
          onChange={handleStartSecondChange}
          InputLabelProps={{ shrink: true }}
          inputProps={{ type: "number", min: 0, max: selectedEndSeconds }}
          sx={{ width: "100%" }}
        />
      </Grid>
    );

    stop = (
      <Grid item xs={6}>
        <TextField
          label="FMU Stop Time"
          value={selectedEndSeconds}
          onChange={handleEndSecondChange}
          InputLabelProps={{ shrink: true }}
          inputProps={{ type: "number", min: selectedStartSeconds }}
          sx={{ width: "100%" }}
        />
      </Grid>
    );
  }

  return (
    <div>
      <Dialog fullWidth={true} maxWidth="sm" open={true} onClose={onClose}>
        <DialogTitle>
          <Grid container justifyContent="space-between" alignItems="center">
            <span>Simulation Parameters</span>
            <IconButton onClick={onClose}>
              <Close />
            </IconButton>
          </Grid>
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} style={{ paddingTop: 8 }}>
            {start}
            {stop}
            <Grid item xs={12}>
              <TextField
                label="Timescale"
                value={timescale}
                onChange={handleTimescaleChange}
                InputLabelProps={{ shrink: true }}
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
                    onChange={(event, checked) => setRealtime(checked)}
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
                    onChange={(event, checked) => setExternalClock(checked)}
                  />
                }
                label="External Clock"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button variant="contained" onClick={onClose}>
            Cancel
          </Button>
          <Button variant="contained" onClick={handleRequestStart} disabled={runDisabled()}>
            Run
          </Button>
        </DialogActions>
      </Dialog>
    </div>
  );
};
