import React, { useEffect, useState } from "react";
import { MoreVert } from "@mui/icons-material";
import { Button, Checkbox, Grid, IconButton, Table, TableBody, TableCell, TableHead, TableRow } from "@mui/material";
import ky from "ky";
import { ErrorDialog } from "./ErrorDialog";
import { PointDialog } from "./PointDialog";
import { StartDialog } from "./StartDialog";

export const Sites = () => {
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState([]);
  const [sites, setSites] = useState([]);
  const [showErrorDialog, setShowErrorDialog] = useState(null);
  const [showPointDialog, setShowPointDialog] = useState(null);
  const [showStartDialog, setShowStartDialog] = useState(null);

  const validStates = {
    start: ["ready"],
    stop: ["preprocessing", "starting", "started", "running", "stopping"],
    remove: ["ready", "complete", "error"]
  };

  const fetchSites = async () => {
    const { data: sites } = await ky("/api/v2/sites").json();
    setSites(sites);
    setLoading(false);
  };

  useEffect(() => {
    fetchSites();
    const id = setInterval(fetchSites, 1000);

    return () => clearInterval(id);
  }, []);

  const isSelected = (siteRef) => selected.includes(siteRef);

  const selectedSites = () => sites.filter(({ id }) => selected.includes(id));

  const handleRowClick = (event, siteRef) => {
    const newSelected = selected.includes(siteRef) ? selected.filter((id) => id !== siteRef) : [...selected, siteRef];
    setSelected(newSelected);
  };

  const isStartButtonDisabled = () => {
    return !selectedSites().some(({ status }) => validStates.start.includes(status));
  };

  const isStopButtonDisabled = () => {
    return !selectedSites().some(({ status }) => validStates.stop.includes(status));
  };

  const isRemoveButtonDisabled = () => {
    return !selectedSites().some(({ status }) => validStates.remove.includes(status));
  };

  const handleOpenErrorDialog = (event, site) => {
    event.stopPropagation();
    setShowErrorDialog(site);
  };

  const handleOpenPointDialog = (event, site) => {
    event.stopPropagation();
    setShowPointDialog(site);
  };

  const handleStartSimulation = (startDatetime, endDatetime, timescale, realtime, externalClock) => {
    selectedSites()
      .filter(({ status }) => validStates.start.includes(status))
      .map(async ({ id }) => {
        await ky
          .post(`/api/v2/sites/${id}/start`, {
            json: {
              startDatetime,
              endDatetime,
              timescale,
              realtime,
              externalClock
            }
          })
          .json();
      });
  };

  const handleStopSimulation = () => {
    selectedSites()
      .filter(({ status }) => validStates.stop.includes(status))
      .map(async ({ id }) => {
        await ky.post(`/api/v2/sites/${id}/stop`).json();
      });
  };

  const handleRemoveSite = () => {
    selectedSites()
      .filter(({ status }) => validStates.remove.includes(status))
      .map(async ({ id }) => {
        await ky.delete(`/api/v2/sites/${id}`).json();
      });
  };

  if (loading) return null;

  return (
    <Grid container direction="column">
      {showErrorDialog && <ErrorDialog site={showErrorDialog} onClose={() => setShowErrorDialog(null)} />}
      {showPointDialog && <PointDialog site={showPointDialog} onClose={() => setShowPointDialog(null)} />}
      {showStartDialog && (
        <StartDialog onStartSimulation={handleStartSimulation} onClose={() => setShowStartDialog(null)} />
      )}
      <Grid item>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell padding="checkbox" />
              <TableCell>Name</TableCell>
              <TableCell>ID</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Time</TableCell>
              <TableCell>Points</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {sites.map((site) => {
              return (
                <TableRow
                  key={site.id}
                  selected={false}
                  style={{ cursor: "default" }}
                  onClick={(event) => handleRowClick(event, site.id)}>
                  <TableCell padding="checkbox">
                    <Checkbox checked={isSelected(site.id)} />
                  </TableCell>
                  <TableCell padding="none">{site.name}</TableCell>
                  <TableCell>{site.id}</TableCell>
                  <TableCell>
                    {site.status === "error" && site.errorLog ? (
                      <Button
                        variant="text"
                        style={{ marginLeft: -9 }}
                        onClick={(event) => handleOpenErrorDialog(event, site)}>
                        {site.status.toUpperCase()}
                      </Button>
                    ) : (
                      site.status.toUpperCase()
                    )}
                  </TableCell>
                  <TableCell>{site.datetime}</TableCell>
                  <TableCell>
                    <IconButton onClick={(event) => handleOpenPointDialog(event, site)}>
                      <MoreVert />
                    </IconButton>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </Grid>
      <Grid item>
        <Grid container justifyContent="flex-start" alignItems="center" style={{ marginLeft: 0, paddingLeft: 16 }}>
          <Grid item>
            <Button
              variant="contained"
              disabled={isStartButtonDisabled()}
              onClick={() => setShowStartDialog(true)}
              sx={{ m: 1 }}>
              Start Test
            </Button>
          </Grid>
          <Grid item>
            <Button variant="contained" disabled={isStopButtonDisabled()} onClick={handleStopSimulation} sx={{ m: 1 }}>
              Stop Test
            </Button>
          </Grid>
          <Grid item>
            <Button variant="contained" disabled={isRemoveButtonDisabled()} onClick={handleRemoveSite} sx={{ m: 1 }}>
              Remove Test Case
            </Button>
          </Grid>
        </Grid>
      </Grid>
    </Grid>
  );
};
