import React, { PropTypes } from 'react';
import Dialog, {
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
} from 'material-ui/Dialog';
import { DateTimePicker } from 'material-ui-pickers'
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
  }

  handleStartDateTimeChange = dateTime => {
    this.setState({ selectedStartDateTime: dateTime })
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

  handleRequestStart = () => {
    this.props.onStartSimulation();
    this.setState({open: false});
  }

  render = () => {
    const { selectedStartDateTime, selectedEndDateTime } = this.state

    return (
      <div>
        <Button raised disabled={this.props.disabled} onTouchTap={this.handleShowDialogClick}>Start Simulation</Button>
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
                  label="Time Multiplier"
                  defaultValue="1"
                  InputLabelProps={{shrink: true, className: this.props.classes.label}}
                  disabled={this.state.realtime}
                  inputProps={{type: 'number', min: 1, max: 200}}
                />
              </Grid>
              <Grid item xs={6}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={this.state.realtime}
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
};

export default withStyles(styles)(StartDialog);

