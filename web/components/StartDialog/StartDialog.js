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
import Dialog from '@material-ui/core/Dialog';
import DialogActions from '@material-ui/core/DialogActions';
import DialogContent from '@material-ui/core/DialogContent';
import DialogContentText from '@material-ui/core/DialogContentText';
import DialogTitle from '@material-ui/core/DialogTitle';
import { DateTimePicker } from 'material-ui-pickers';
import { withStyles } from '@material-ui/core/styles';
import Button from '@material-ui/core/Button';
import Grid from '@material-ui/core/Grid';
import TextField from '@material-ui/core/TextField';
import FormControlLabel from '@material-ui/core/FormControlLabel';
import Switch from '@material-ui/core/Switch';

const styles = theme => ({
  label: {
   whiteSpace: 'nowrap' 
  },
  button: {
    margin: theme.spacing.unit,
  },
});

class StartDialog extends React.Component {
  constructor(props) {
    super(props);

    this.state = {
      open: false,
      realtime: false,
      timescale: 5,
      selectedStartTime: 0,
      selectedEndTime: 86400
    };
  }

  //componentWillMount = () => {
  //  console.log(this.props);
  //  if ( this.props.type == 'osm' ) {
  //    this.state.selectedStartTime = new Date();
  //    this.state.selectedEndTime = new Date();
  //  } else {
  //    this.state.selectedStartTime = 0;
  //    this.state.selectedEndTime = 86400;
  //  }
  //}

  handleStartTimeChange = time => {
    this.setState({ selectedStartTime: time })
  }

  handleTimescaleChange = event => {
    this.setState({ timescale: event.target.value })
  }

  handleEndTimeChange = time => {
    this.setState({ selectedEndTime: time })
  }

  handleShowDialogClick = () => {
    this.setState({open: true});
  }

  handleRequestClose = () => {
    this.setState({open: false});
  }

  handleRequestStart = () => {
    this.props.onStartSimulation(this.state.selectedStartTime,this.state.selectedEndTime,this.state.timescale,this.state.realtime);
    this.setState({open: false});
  }

  render = () => {
    const { selectedStartTime, selectedEndTime, realtime, timescale } = this.state
    const { classes, type } = this.props;

    console.log("startDialogType: ", this.props.type);

    let start;
    let stop;
    if ( this.props.type == 'osm' ) {
      start = 
      <Grid item xs={6}>
        <DateTimePicker
          value={selectedStartTime}
          onChange={this.handleStartTimeChange}
          label="EnergyPlus Start Time"
          disabled={this.state.realtime}
        />
      </Grid>;

      stop = 
      <Grid item xs={6}>
        <DateTimePicker
          value={selectedEndTime}
          onChange={this.handleEndTimeChange}
          label="EnergyPlus End Time"
          disabled={this.state.realtime}
        />
      </Grid>;
    } else {
      start = 
      <Grid item xs={6}>
        <TextField 
          label="FMU Start Time"
          value={selectedStartTime}
          onChange={this.handleStartTimeChange}
          InputLabelProps={{shrink: true, className: this.props.classes.label}}
          disabled={realtime}
          inputProps={{type: 'number', max: selectedEndTime}}
        />
      </Grid>;

      stop = 
      <Grid item xs={6}>
        <TextField 
          label="FMU Stop Time"
          value={selectedEndTime}
          onChange={this.handleEndTimeChange}
          InputLabelProps={{shrink: true, className: this.props.classes.label}}
          disabled={realtime}
          inputProps={{type: 'number', min: selectedStartTime}}
        />
      </Grid>;
    }

    return (
      <div>
        <Button className={classes.button} variant="contained" disabled={this.props.disabled} onClick={this.handleShowDialogClick}>Start Simulation</Button>
        <Dialog fullWidth={true} open={this.state.open}>
          <DialogTitle>Simulation Parameters</DialogTitle>
          <DialogContent>
            <Grid container spacing={16}>
              {start}
              {stop}
              <Grid item xs={6}>
                <TextField 
                  label="Timescale"
                  value={this.state.timescale}
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
                      disabled={false}
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

