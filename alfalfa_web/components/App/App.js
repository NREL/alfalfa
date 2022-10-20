import { AdapterLuxon } from "@mui/x-date-pickers/AdapterLuxon";
import { LocalizationProvider } from "@mui/x-date-pickers/LocalizationProvider";
import { AppBar, Grid, Toolbar, Typography } from "@mui/material";
import { createTheme, ThemeProvider } from "@mui/material/styles";
import { withStyles } from "@mui/styles";
import PropTypes from "prop-types";
import React from "react";
import { Link, Navigate, Route, Routes } from "react-router-dom";
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
                    <Link to={"/sites"} style={{ textDecoration: "none", color: "unset" }}>
                      <Typography className={classes.button} variant="button" color="inherit">
                        Sites
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
              <Route path="/sites" element={<Sites />} />
              <Route path="/sims" element={<Sims />} />
              <Route path="*" element={<Navigate to="/" />} />
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
