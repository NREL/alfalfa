import React, { useEffect, useState } from "react";
import { Delete, Download, InfoOutlined, Insights, MoreVert, PlayArrow, Stop, Visibility } from "@mui/icons-material";
import {
  Button,
  Checkbox,
  Divider,
  Grid,
  IconButton,
  ListItemIcon,
  ListItemText,
  Menu,
  MenuItem,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TableSortLabel
} from "@mui/material";
import ky from "ky";
import { DateTime } from "luxon";
import { ErrorDialog } from "./ErrorDialog";
import { NoticeDialog } from "./NoticeDialog";
import { PointDialog } from "./PointDialog";
import { StartDialog } from "./StartDialog";

const columns = [
  { id: "name", label: "Name" },
  { id: "id", label: "ID" },
  { id: "status", label: "Status" },
  { id: "datetime", label: "Time" },
  { id: "uploadTimestamp", label: "Uploaded" }
];

// Matches the "y-LL-dd HH:mm:ss" format start/end datetimes are submitted in
// (see StartDialog) and stored/interpreted as UTC by the historian.
const simDatetimeFormat = "y-LL-dd HH:mm:ss";

const formatUploadTimestamp = (timestamp) => {
  if (!timestamp) return "";
  return DateTime.fromISO(timestamp).toFormat("y-LL-dd HH:mm:ss");
};

// Builds a Grafana URL for the historian dashboard, pre-scoped to this run's
// id and simulated time window.
const buildHistorianUrl = (run, historianConfig) => {
  const base = historianConfig.grafanaUrl.replace(/\/+$/, "");
  const params = new URLSearchParams({ orgId: "1", "var-run_id": run.id });
  // Auto-refresh only while the simulation is actively running; a finished/not-yet-started
  // run has no new data coming in, so a static view is more appropriate.
  if (run.status === "RUNNING") params.set("refresh", "5s");

  if (run.simDatetimeStart) {
    const from = DateTime.fromFormat(run.simDatetimeStart, simDatetimeFormat, { zone: "utc" });
    if (from.isValid) params.set("from", from.toMillis());
  }
  if (run.simDatetimeEnd) {
    const to = DateTime.fromFormat(run.simDatetimeEnd, simDatetimeFormat, { zone: "utc" });
    if (to.isValid) params.set("to", to.toMillis());
  }

  return `${base}${historianConfig.grafanaDashboardPath}?${params.toString()}`;
};

// Persist the selected sort column/direction across navigation and reloads.
const SORT_STORAGE_KEY = "alfalfa.sites.sort";

const loadStoredSort = () => {
  try {
    const stored = JSON.parse(localStorage.getItem(SORT_STORAGE_KEY));
    if (stored && columns.some(({ id }) => id === stored.orderBy) && ["asc", "desc"].includes(stored.order)) {
      return stored;
    }
  } catch {
    // ignore malformed/missing storage and fall back to defaults
  }
  return { orderBy: null, order: "asc" };
};

export const Sites = ({ historianConfig = { historianEnabled: false, grafanaUrl: "", grafanaDashboardPath: "" } }) => {
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState([]);
  const [runs, setRuns] = useState([]);
  const [showErrorDialog, setShowErrorDialog] = useState(null);
  const [showNoticeDialog, setShowNoticeDialog] = useState(null);
  const [showPointDialog, setShowPointDialog] = useState(null);
  // Holds the run(s) targeted by the Start dialog, whether opened via the bulk
  // "Start Test" button (checkbox selection) or a single row's menu item.
  const [startDialogTargets, setStartDialogTargets] = useState(null);
  const [rowMenuAnchorEl, setRowMenuAnchorEl] = useState(null);
  const [rowMenuRun, setRowMenuRun] = useState(null);
  const [{ orderBy, order }, setSort] = useState(loadStoredSort);

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

  const isAllSelected = () => runs.length > 0 && selected.length === runs.length;

  const isSomeSelected = () => selected.length > 0 && selected.length < runs.length;

  const handleSelectAll = (event) => {
    setSelected(event.target.checked ? runs.map(({ id }) => id) : []);
  };

  const handleSort = (columnId) => {
    setSort((current) => {
      const next =
        current.orderBy === columnId
          ? { orderBy: columnId, order: current.order === "asc" ? "desc" : "asc" }
          : { orderBy: columnId, order: "asc" };
      localStorage.setItem(SORT_STORAGE_KEY, JSON.stringify(next));
      return next;
    });
  };

  const sortedRuns = () => {
    if (!orderBy) return runs;
    const direction = order === "asc" ? 1 : -1;
    return [...runs].sort((a, b) => {
      const aValue = a[orderBy];
      const bValue = b[orderBy];
      if (aValue == null && bValue == null) return 0;
      if (aValue == null) return 1;
      if (bValue == null) return -1;
      if (typeof aValue === "string" && typeof bValue === "string") {
        return direction * aValue.localeCompare(bValue, undefined, { numeric: true, sensitivity: "base" });
      }
      if (aValue < bValue) return -direction;
      if (aValue > bValue) return direction;
      return 0;
    });
  };

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

  const handleOpenNoticeDialog = (event, run) => {
    event.stopPropagation();
    setShowNoticeDialog(run);
  };

  const handleOpenRowMenu = (event, run) => {
    event.stopPropagation();
    setRowMenuAnchorEl(event.currentTarget);
    setRowMenuRun(run);
  };

  const handleCloseRowMenu = () => {
    setRowMenuAnchorEl(null);
    setRowMenuRun(null);
  };

  const handleOpenPointDialog = (run) => {
    setShowPointDialog(run);
    handleCloseRowMenu();
  };

  const handleOpenHistorian = (run) => {
    window.open(buildHistorianUrl(run, historianConfig), "_blank", "noopener,noreferrer");
    handleCloseRowMenu();
  };

  const handleStartSimulation = (startDatetime, endDatetime, timescale, realtime, externalClock) => {
    (startDialogTargets || [])
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

  const handleStopSimulation = (targetRuns = selectedRuns()) => {
    targetRuns
      .filter(({ status }) => validStates.stop.includes(status))
      .map(async ({ id }) => {
        await ky.post(`/api/v2/runs/${id}/stop`).json();
      });
    handleCloseRowMenu();
  };

  const handleRemoveRun = (targetRuns = selectedRuns()) => {
    targetRuns
      .filter(({ status }) => validStates.remove.includes(status))
      .map(async ({ id }) => {
        await ky.delete(`/api/v2/runs/${id}`).json();
      });
    handleCloseRowMenu();
  };

  const handleDownloadRun = async (targetRuns = selectedRuns()) => {
    const ids = targetRuns.filter(({ status }) => validStates.download.includes(status)).map(({ id }) => id);

    for (const id of ids) {
      location.href = `/api/v2/runs/${id}/download`;
      await new Promise((resolve) => setTimeout(resolve, 500));
    }
    handleCloseRowMenu();
  };

  if (loading) return null;

  return (
    <Grid container direction="column">
      {showErrorDialog && <ErrorDialog run={showErrorDialog} onClose={() => setShowErrorDialog(null)} />}
      {showNoticeDialog && <NoticeDialog run={showNoticeDialog} onClose={() => setShowNoticeDialog(null)} />}
      {showPointDialog && <PointDialog run={showPointDialog} onClose={() => setShowPointDialog(null)} />}
      {startDialogTargets && (
        <StartDialog onStartSimulation={handleStartSimulation} onClose={() => setStartDialogTargets(null)} />
      )}
      <Menu anchorEl={rowMenuAnchorEl} open={Boolean(rowMenuAnchorEl)} onClose={handleCloseRowMenu}>
        <MenuItem onClick={() => handleOpenPointDialog(rowMenuRun)}>
          <ListItemIcon>
            <Visibility fontSize="small" />
          </ListItemIcon>
          <ListItemText>Inspect Points</ListItemText>
        </MenuItem>
        <Divider />
        <MenuItem
          disabled={!rowMenuRun || !validStates.start.includes(rowMenuRun.status)}
          onClick={() => {
            setStartDialogTargets([rowMenuRun]);
            handleCloseRowMenu();
          }}>
          <ListItemIcon>
            <PlayArrow fontSize="small" />
          </ListItemIcon>
          <ListItemText>Start</ListItemText>
        </MenuItem>
        <MenuItem
          disabled={!rowMenuRun || !validStates.stop.includes(rowMenuRun.status)}
          onClick={() => handleStopSimulation([rowMenuRun])}>
          <ListItemIcon>
            <Stop fontSize="small" />
          </ListItemIcon>
          <ListItemText>Stop</ListItemText>
        </MenuItem>
        <MenuItem
          disabled={!rowMenuRun || !validStates.remove.includes(rowMenuRun.status)}
          onClick={() => handleRemoveRun([rowMenuRun])}>
          <ListItemIcon>
            <Delete fontSize="small" />
          </ListItemIcon>
          <ListItemText>Remove</ListItemText>
        </MenuItem>
        <MenuItem
          disabled={!rowMenuRun || !validStates.download.includes(rowMenuRun.status)}
          onClick={() => handleDownloadRun([rowMenuRun])}>
          <ListItemIcon>
            <Download fontSize="small" />
          </ListItemIcon>
          <ListItemText>Download</ListItemText>
        </MenuItem>
        {historianConfig.historianEnabled && historianConfig.grafanaUrl && (
          <React.Fragment>
            <Divider />
            <MenuItem onClick={() => handleOpenHistorian(rowMenuRun)}>
              <ListItemIcon>
                <Insights fontSize="small" />
              </ListItemIcon>
              <ListItemText>Open in Historian</ListItemText>
            </MenuItem>
          </React.Fragment>
        )}
      </Menu>
      <Grid item>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell padding="checkbox">
                <Checkbox checked={isAllSelected()} indeterminate={isSomeSelected()} onChange={handleSelectAll} />
              </TableCell>
              {columns.map((column) => (
                <TableCell key={column.id}>
                  <TableSortLabel
                    active={orderBy === column.id}
                    direction={orderBy === column.id ? order : "asc"}
                    onClick={() => handleSort(column.id)}>
                    {column.label}
                  </TableSortLabel>
                </TableCell>
              ))}
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {sortedRuns().map((run) => {
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
                    {run.status === "ERROR" && run.errorLog ? (
                      <Button
                        variant="text"
                        style={{ marginLeft: -9 }}
                        onClick={(event) => handleOpenErrorDialog(event, run)}>
                        {run.status.toUpperCase()}
                      </Button>
                    ) : (
                      run.status.toUpperCase()
                    )}
                    {run.notices && run.notices.length > 0 && (
                      <IconButton
                        size="small"
                        title="This run has notices"
                        onClick={(event) => handleOpenNoticeDialog(event, run)}>
                        <InfoOutlined fontSize="small" color="info" />
                      </IconButton>
                    )}
                  </TableCell>
                  <TableCell>{run.datetime}</TableCell>
                  <TableCell>{formatUploadTimestamp(run.uploadTimestamp)}</TableCell>
                  <TableCell>
                    <IconButton onClick={(event) => handleOpenRowMenu(event, run)}>
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
              onClick={() => setStartDialogTargets(selectedRuns())}
              sx={{ m: 1 }}>
              Start Test
            </Button>
          </Grid>
          <Grid item>
            <Button
              variant="contained"
              disabled={isStopButtonDisabled()}
              onClick={() => handleStopSimulation()}
              sx={{ m: 1 }}>
              Stop Test
            </Button>
          </Grid>
          <Grid item>
            <Button
              variant="contained"
              disabled={isRemoveButtonDisabled()}
              onClick={() => handleRemoveRun()}
              sx={{ m: 1 }}>
              Remove Test Case(s)
            </Button>
          </Grid>
          <Grid item>
            <Button
              variant="contained"
              disabled={isDownloadButtonDisabled()}
              onClick={() => handleDownloadRun()}
              sx={{ m: 1 }}>
              Download Run
            </Button>
          </Grid>
        </Grid>
      </Grid>
    </Grid>
  );
};
