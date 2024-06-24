import React from "react";
import { AdapterLuxon } from "@mui/x-date-pickers/AdapterLuxon";
import { LocalizationProvider } from "@mui/x-date-pickers/LocalizationProvider";
import { AppBar, Grid, Toolbar, Typography } from "@mui/material";
import { createTheme, ThemeProvider } from "@mui/material/styles";
import { Link, Navigate, Route, Routes } from "react-router-dom";
import { Docs } from "../Docs/Docs";
import { Runs } from "../Runs/Runs";
import { Upload } from "../Upload/Upload";
import styles from "./App.scss";

const theme = createTheme();

export const App = () => {
  return (
    <ThemeProvider theme={theme}>
      <LocalizationProvider dateAdapter={AdapterLuxon}>
        <div className={styles.root}>
          <AppBar position="static" sx={{ zIndex: 1 }}>
            <Toolbar>
              <Link to={"/"} className={styles.title} style={{ textDecoration: "none", color: "unset" }}>
                <Typography variant="h5" color="inherit">
                  Alfalfa
                </Typography>
              </Link>
              <Grid container justifyContent="flex-end" spacing={2} style={{ marginLeft: 0 }}>
                <Grid item>
                  <Link to={"/runs"} style={{ textDecoration: "none", color: "unset" }}>
                    <Typography variant="button" color="inherit" sx={{ m: 1 }}>
                      Runs
                    </Typography>
                  </Link>
                </Grid>
                <Grid item>
                  <Link to={"/docs"} style={{ textDecoration: "none", color: "unset" }}>
                    <Typography variant="button" color="inherit" sx={{ m: 1 }}>
                      API Docs
                    </Typography>
                  </Link>
                </Grid>
              </Grid>
            </Toolbar>
          </AppBar>
          <Routes>
            <Route path="/" element={<Upload />} />
            <Route path="/runs" element={<Runs />} />
            <Route path="/docs" element={<Docs />} />
            <Route path="*" element={<Navigate to="/" />} />
          </Routes>
        </div>
      </LocalizationProvider>
    </ThemeProvider>
  );
};
