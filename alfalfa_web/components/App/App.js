/***********************************************************************************************************************
 *  Copyright (c) 2008-2022, Alliance for Sustainable Energy, LLC, and other contributors. All rights reserved.
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

import { AdapterLuxon } from "@mui/x-date-pickers/AdapterLuxon";
import { LocalizationProvider } from "@mui/x-date-pickers/LocalizationProvider";
import { AppBar, Grid, Toolbar, Typography } from "@mui/material";
import { createTheme, ThemeProvider } from "@mui/material/styles";
import { withStyles } from "@mui/styles";
import PropTypes from "prop-types";
import React from "react";
import { Link, Route, Routes } from "react-router-dom";
import Sims from "../Sims/Sims";
import Sites from "../Sites/Sites";
import Upload from "../Upload/Upload";

const theme = createTheme();

const styles = {
  root: {
    display: "flex",
    flexDirection: "column",
    minHeight: "100vh"
  },
  title: {
    flex: 1
  },
  button: {
    margin: `${theme.spacing(1)}!important`
  }
};

class App extends React.Component {
  render = () => {
    const { classes } = this.props;

    return (
      <ThemeProvider theme={theme}>
        <LocalizationProvider dateAdapter={AdapterLuxon}>
          <div className={this.props.classes.root}>
            <AppBar position="static">
              <Toolbar>
                <Link to={"/"} className={this.props.classes.title} style={{ textDecoration: "none", color: "unset" }}>
                  <Typography variant="h5" color="inherit">
                    Alfalfa
                  </Typography>
                </Link>
                <Grid container justifyContent="flex-end" spacing={2} style={{ marginLeft: 0 }}>
                  <Grid item>
                    <Link to={"/models"} style={{ textDecoration: "none", color: "unset" }}>
                      <Typography className={classes.button} variant="button" color="inherit">
                        Models
                      </Typography>
                    </Link>
                  </Grid>
                  <Grid item>
                    <Link to={"/sims"} style={{ textDecoration: "none", color: "unset" }}>
                      <Typography className={classes.button} variant="button" color="inherit">
                        Completed-Simulations
                      </Typography>
                    </Link>
                  </Grid>
                </Grid>
              </Toolbar>
            </AppBar>
            <Routes>
              <Route path="/" element={<Upload />} />
              <Route path="models" element={<Sites />} />
              <Route path="sims" element={<Sims />} />
            </Routes>
          </div>
        </LocalizationProvider>
      </ThemeProvider>
    );
  };
}

App.propTypes = {
  classes: PropTypes.object.isRequired
};

export default withStyles(styles)(App);
