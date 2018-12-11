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
import Grid from '@material-ui/core/Grid';
import { graphql } from 'react-apollo';
import gql from 'graphql-tag';
import Table from '@material-ui/core/Table';
import TableBody from '@material-ui/core/TableBody';
import TableCell from '@material-ui/core/TableCell';
import TableHead from '@material-ui/core/TableHead';
import TableRow from '@material-ui/core/TableRow';
import Checkbox from '@material-ui/core/Checkbox';
import { withStyles } from '@material-ui/core/styles';
import downloadjs from 'downloadjs'

class Sims extends React.Component {

  state = {
    selected: [],
  };

  isSelected = (simRef) => {
    return this.state.selected.indexOf(simRef) !== -1;
  };

  selectedSims = () => {
    return this.props.data.viewer.sims.filter((sim) => {
      return this.state.selected.some((simRef) => {
        return (simRef === sim.simRef);
      })
    });
  }

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
      newSelected = newSelected.concat(
        selected.slice(0, selectedIndex),
        selected.slice(selectedIndex + 1),
      );
    }

    this.setState({ selected: newSelected });
  };

  buttonsDisabled = () => {
    return (this.state.selected.length == 0);
  }

  handleRemove = () => {
    console.log("Handle Remove");
  }

  handleDownload = () => {
    this.selectedSims().map((sim) => {
      let url = new URL(sim.url);
      let local_s3 = true;
      if ( local_s3 ) {
        url.hostname = window.location.hostname;
        url.pathname = '/alfalfa' + url.pathname;
      }
      var xhr = new XMLHttpRequest();
      xhr.open('GET', url, true);
      xhr.responseType = 'blob';
      xhr.onload = (e) => { 
			  downloadjs(e.target.response, sim.name + '.tar.gz');
			};
      xhr.send();
    })
  }

  render = () => {
    const { classes } = this.props;

    if( ! this.props.data.loading ) {
      const sims = this.props.data.viewer.sims;
      const buttonsDisabled = this.buttonsDisabled();
      return (
        <Grid container direction="column">
          <Grid item>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell padding="checkbox"></TableCell>
                  <TableCell>Name</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Completed Time</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {sims.map((sim) => {
                  const isSelected = this.isSelected(sim.simRef);
                  return (
                   <TableRow key={sim.simRef}
                     onClick={event => this.handleRowClick(event, sim.simRef)}
                   >
                     <TableCell padding="checkbox">
                       <Checkbox
                         checked={isSelected}
                       />
                     </TableCell>
                     <TableCell padding="none">{sim.name}</TableCell>
                     <TableCell padding="none">{sim.simStatus}</TableCell>
                     <TableCell>{sim.timeCompleted}</TableCell>
                   </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </Grid>
          <Grid item>
            <Grid className={classes.controls} container justify="flex-start" alignItems="center" >
              <Grid item>
                <Button className={classes.button} variant="contained" disabled={true} onClick={this.handleRemove}>Remove Simulation</Button>
              </Grid>
              <Grid item>
                <Button className={classes.button} variant="contained" disabled={buttonsDisabled} onClick={this.handleDownload}>Download Simulation</Button>
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

const simsQL = gql`
  query SimsQuery {
    viewer {
      sims {
        simRef,
        name,
        simStatus,
        siteRef,
        url,
        timeCompleted
      }
    }
  }
`;

const withSims = graphql(simsQL, {
  options: { 
    pollInterval: 1000,
  }
})(Sims);

const styles = theme => ({
  controls: {
    marginLeft: 16,
  },
  button: {
    margin: theme.spacing.unit,
  },
});

const withStyle = withStyles(styles)(withSims);

export default withStyle;

