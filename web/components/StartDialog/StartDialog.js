import React, { PropTypes } from 'react';
import Dialog, {
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
} from 'material-ui/Dialog';
import { DateTimePicker } from 'material-ui-pickers';
import { withStyles } from 'material-ui/styles';
import Button from 'material-ui/Button';
import Grid from 'material-ui/Grid';
import TextField from 'material-ui/TextField';
import { FormControlLabel } from 'material-ui/Form';
import Switch from 'material-ui/Switch';

const styles = {
  label: {
   whiteSpace: 'nowrap' 
  },
};

class StartDialog extends React.Component {
  state = {
    open: false,
    selectedStartDateTime: new Date(),
    selectedEndDateTime: new Date(),
    realtime: false,
    timescale: 120,
  }

  handleStartDateTimeChange = dateTime => {
    this.setState({ selectedStartDateTime: dateTime })
  }

  handleTimescaleChange = scale => {
    this.setState({ timescale: scale })
  }

  handleEndDateTimeChange = dateTime => {
    this.setState({ selectedEndDateTime: dateTime })
  }

  handleShowDialogClick = () => {
    this.setState({open: true});
  }

  handleRequestClose = () => {
    this.setState({open: false});
  }

  //startSimProp: (siteRef, startDatetime, endDatetime, timescale, realtime) => mutate({ variables: { siteRef, startDatetime, endDatetime, timescale, realtime } }),
  handleRequestStart = () => {
    this.props.onStartSimulation(this.state.selectedStartDateTime,this.state.selectedEndDateTime,this.state.timescale,this.state.realtime);
    this.setState({open: false});
  }

  render = () => {
    const { selectedStartDateTime, selectedEndDateTime, realtime, timescale } = this.state

    return (
      <div>
        <Button raised disabled={this.props.disabled} onClick={this.handleShowDialogClick}>Start Simulation</Button>
        <Dialog fullWidth={true} open={this.state.open}>
          <DialogTitle>Simulation Parameters</DialogTitle>
          <DialogContent>
            <Grid container>
              <Grid item xs={6}>
                <DateTimePicker
                  value={selectedStartDateTime}
                  onChange={this.handleStartDateTimeChange}
                  label="Begin"
                  disabled={this.state.realtime}
                />
              </Grid>
              <Grid item xs={6}>
                <DateTimePicker
                  value={selectedEndDateTime}
                  onChange={this.handleEndDateTimeChange}
                  label="End"
                  disabled={this.state.realtime}
                />
              </Grid>
              <Grid item xs={6}>
                <TextField 
                  label="Timescale"
                  value={timescale}
                  onChange={this.handleTimescaleChange}
                  InputLabelProps={{shrink: true, className: this.props.classes.label}}
                  disabled={this.state.realtime}
                  inputProps={{type: 'number', min: 1, max: 200}}
                />
              </Grid>
              <Grid item xs={6}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={realtime}
                      disabled={true}
                      onChange={(event, checked) => this.setState({ realtime: checked })}
                    />
                  }
                  label="Realtime Simulation"
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
  }
}

export default withStyles(styles)(StartDialog);

