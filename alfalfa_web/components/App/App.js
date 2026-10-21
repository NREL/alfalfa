import React, { useEffect, useState } from "react";
import { AdapterLuxon } from "@mui/x-date-pickers/AdapterLuxon";
import { LocalizationProvider } from "@mui/x-date-pickers/LocalizationProvider";
import { AppBar, Grid, Toolbar, Typography } from "@mui/material";
import { createTheme, ThemeProvider } from "@mui/material/styles";
import ky from "ky";
import { Link, Navigate, Route, Routes } from "react-router-dom";
import { Docs } from "../Docs/Docs";
import { Sims } from "../Sims/Sims";
import { Sites } from "../Sites/Sites";
import { Upload } from "../Upload/Upload";
import styles from "./App.scss";

const theme = createTheme();

export const App = () => {
  const [historianConfig, setHistorianConfig] = useState({ historianEnabled: false, grafanaUrl: "" });

  useEffect(() => {
    const fetchConfig = async () => {
      try {
        const { payload } = await ky("/api/v2/config").json();
        setHistorianConfig(payload);
      } catch (err) {
        console.error("Failed to fetch config", err);
      }
    };

    fetchConfig();
  }, []);

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
                  <Link to={"/sites"} style={{ textDecoration: "none", color: "unset" }}>
                    <Typography variant="button" color="inherit" sx={{ m: 1 }}>
                      Sites
                    </Typography>
                  </Link>
                </Grid>
                <Grid item>
                  <Link to={"/sims"} style={{ textDecoration: "none", color: "unset" }}>
                    <Typography variant="button" color="inherit" sx={{ m: 1 }}>
                      Completed Simulations
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
                {historianConfig.historianEnabled && historianConfig.grafanaUrl && (
                  <Grid item>
                    <a
                      href={historianConfig.grafanaUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{ textDecoration: "none", color: "unset" }}>
                      <Typography variant="button" color="inherit" sx={{ m: 1 }}>
                        Historian
                      </Typography>
                    </a>
                  </Grid>
                )}
              </Grid>
            </Toolbar>
          </AppBar>
          <Routes>
            <Route path="/" element={<Upload />} />
            <Route path="/sites" element={<Sites historianConfig={historianConfig} />} />
            <Route path="/sims" element={<Sims />} />
            <Route path="/docs" element={<Docs />} />
            <Route path="*" element={<Navigate to="/" />} />
          </Routes>
        </div>
      </LocalizationProvider>
    </ThemeProvider>
  );
};
