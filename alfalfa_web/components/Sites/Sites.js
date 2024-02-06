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
  const [runs, setRuns] = useState([]);
  const [showErrorDialog, setShowErrorDialog] = useState(null);
  const [showPointDialog, setShowPointDialog] = useState(null);
  const [showStartDialog, setShowStartDialog] = useState(null);

  const validStates = {
    start: ["READY"],
    stop: ["PREPROCESSING", "STARTING", "STARTED", "RUNNING", "STOPPING"],
    remove: ["READY", "COMPLETE", "ERROR"],
    download: ["READY", "COMPLETE", "ERROR"]
  };

  const fetchRuns = async () => {
    const { payload: runs } = await ky("/api/v2/runs").json();
    setRuns(runs);
    setLoading(false);
  };

  useEffect(() => {
    fetchRuns();
    const id = setInterval(fetchRuns, 1000);

    return () => clearInterval(id);
  }, []);

  const isSelected = (runId) => selected.includes(runId);

  const selectedRuns = () => runs.filter(({ id }) => selected.includes(id));

  const handleRowClick = (event, runId) => {
    const newSelected = selected.includes(runId) ? selected.filter((id) => id !== runId) : [...selected, runId];
    setSelected(newSelected);
  };

  const isStartButtonDisabled = () => {
    return !selectedRuns().some(({ status }) => validStates.start.includes(status));
  };

  const isStopButtonDisabled = () => {
    return !selectedRuns().some(({ status }) => validStates.stop.includes(status));
  };

  const isRemoveButtonDisabled = () => {
    return !selectedRuns().some(({ status }) => validStates.remove.includes(status));
  };

  const isDownloadButtonDisabled = () => {
    return !selectedRuns().some(({ status }) => validStates.download.includes(status));
  };

  const handleOpenErrorDialog = (event, run) => {
    event.stopPropagation();
    setShowErrorDialog(run);
  };

  const handleOpenPointDialog = (event, run) => {
    event.stopPropagation();
    setShowPointDialog(run);
  };

  const handleStartSimulation = (startDatetime, endDatetime, timescale, realtime, externalClock) => {
    selectedRuns()
      .filter(({ status }) => validStates.start.includes(status))
      .map(async ({ id }) => {
        await ky
          .post(`/api/v2/runs/${id}/start`, {
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
    selectedRuns()
      .filter(({ status }) => validStates.stop.includes(status))
      .map(async ({ id }) => {
        await ky.post(`/api/v2/runs/${id}/stop`).json();
      });
  };

  const handleRemoveRun = () => {
    selectedRuns()
      .filter(({ status }) => validStates.remove.includes(status))
      .map(async ({ id }) => {
        await ky.delete(`/api/v2/runs/${id}`).json();
      });
  };

  const handleDownloadRun = async () => {
    const ids = selectedRuns()
      .filter(({ status }) => validStates.download.includes(status))
      .map(({ id }) => id);

    for (const id of ids) {
      location.href = `/api/v2/runs/${id}/download`;
      await new Promise((resolve) => setTimeout(resolve, 500));
    }
  };

  if (loading) return null;

  return (
    <Grid container direction="column">
      {showErrorDialog && <ErrorDialog run={showErrorDialog} onClose={() => setShowErrorDialog(null)} />}
      {showPointDialog && <PointDialog run={showPointDialog} onClose={() => setShowPointDialog(null)} />}
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
            {runs.map((run) => {
              return (
                <TableRow
                  key={run.id}
                  selected={false}
                  style={{ cursor: "default" }}
                  onClick={(event) => handleRowClick(event, run.id)}>
                  <TableCell padding="checkbox">
                    <Checkbox checked={isSelected(run.id)} />
                  </TableCell>
                  <TableCell padding="none">{run.name}</TableCell>
                  <TableCell>{run.id}</TableCell>
                  <TableCell>
                    {run.status === "error" && run.errorLog ? (
                      <Button
                        variant="text"
                        style={{ marginLeft: -9 }}
                        onClick={(event) => handleOpenErrorDialog(event, run)}>
                        {run.status.toUpperCase()}
                      </Button>
                    ) : (
                      run.status.toUpperCase()
                    )}
                  </TableCell>
                  <TableCell>{run.datetime}</TableCell>
                  <TableCell>
                    <IconButton onClick={(event) => handleOpenPointDialog(event, run)}>
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
            <Button variant="contained" disabled={isRemoveButtonDisabled()} onClick={handleRemoveRun} sx={{ m: 1 }}>
              Remove Test Case
            </Button>
          </Grid>
          <Grid item>
            <Button variant="contained" disabled={isDownloadButtonDisabled()} onClick={handleDownloadRun} sx={{ m: 1 }}>
              Download Run
            </Button>
          </Grid>
        </Grid>
      </Grid>
    </Grid>
  );
};
