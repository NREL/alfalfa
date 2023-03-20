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

export const StartDialog = ({ onClose, onStartSimulation }) => {
  const timeFormat = "y-LL-dd HH:mm:ss";

  const currentTime = DateTime.now();
  const [realtime, setRealtime] = useState(false);
  const [externalClock, setExternalClock] = useState(false);
  const [timescale, setTimescale] = useState(5);
  const [selectedStartTime, setSelectedStartTime] = useState(currentTime);
  const [selectedEndTime, setSelectedEndTime] = useState(currentTime);

  const handleTimescaleChange = (event) => {
    setTimescale(Number(event.target.value));
  };

  const handleRequestStart = () => {
    onStartSimulation(
      selectedStartTime.toFormat(timeFormat),
      selectedEndTime.toFormat(timeFormat),
      timescale,
      realtime,
      externalClock
    );
    onClose();
  };

  const runDisabled = () => selectedEndTime < selectedStartTime;

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
            <Grid item xs={6}>
              <DateTimePicker
                label="Start Time"
                format={timeFormat}
                value={selectedStartTime}
                onChange={setSelectedStartTime}
                slotProps={{ textField: { sx: { width: "100%" } } }}
              />
            </Grid>
            <Grid item xs={6}>
              <DateTimePicker
                label="End Time"
                format={timeFormat}
                value={selectedEndTime}
                onChange={setSelectedEndTime}
                slotProps={{ textField: { sx: { width: "100%" } } }}
              />
            </Grid>
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
