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
import Dialog, {
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
} from '@material-ui/core/Dialog';
import { DateTimePicker } from 'material-ui-pickers';
import { withStyles } from '@material-ui/core/styles';
import Button from '@material-ui/core/Button';
import Grid from '@material-ui/core/Grid';
import TextField from '@material-ui/core/TextField';
import FormControlLabel from '@material-ui/core/FormControlLabel';
import Switch from '@material-ui/core/Switch';

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
    timescale: 5,
  }

  handleStartDateTimeChange = dateTime => {
    this.setState({ selectedStartDateTime: dateTime })
  }

  handleTimescaleChange = event => {
    this.setState({ timescale: event.target.value })
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

