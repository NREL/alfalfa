import React, { useEffect, useState } from "react";
import { Close, ExpandMore } from "@mui/icons-material";
import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Alert,
  Box,
  Button,
  CircularProgress,
  Dialog,
  DialogContent,
  DialogTitle,
  Grid,
  IconButton,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography
} from "@mui/material";
import ky from "ky";

const WRITABLE_TYPES = ["INPUT", "BIDIRECTIONAL"];

const formatRange = (point) => {
  const hasMin = typeof point.min === "number";
  const hasMax = typeof point.max === "number";
  if (!hasMin && !hasMax) return null;
  const unitsSuffix = point.units ? ` ${point.units}` : "";
  return `Valid range: ${hasMin ? point.min : "\u2212\u221e"} to ${hasMax ? point.max : "\u221e"}${unitsSuffix}`;
};

const PointWriteControl = ({ run, point }) => {
  const [value, setValue] = useState("");
  const [saving, setSaving] = useState(false);
  const [feedback, setFeedback] = useState(null);

  const range = formatRange(point);

  const writeValue = async (newValue) => {
    setSaving(true);
    setFeedback(null);
    try {
      await ky.put(`/api/v2/runs/${run.id}/points/${point.id}`, { json: { value: newValue } });
      setFeedback({ severity: "success", message: newValue === null ? "Override cleared" : "Value set" });
    } catch (err) {
      const body = await err.response?.json().catch(() => null);
      setFeedback({ severity: "error", message: body?.message || "Failed to write value" });
    } finally {
      setSaving(false);
    }
  };

  const handleSet = () => {
    const number = Number(value);
    if (value === "" || Number.isNaN(number)) {
      setFeedback({ severity: "error", message: "Enter a numeric value" });
      return;
    }
    writeValue(number);
  };

  const handleClear = () => {
    setValue("");
    writeValue(null);
  };

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 1, mt: 2 }}>
      <Box sx={{ display: "flex", alignItems: "flex-start", gap: 2 }}>
        <TextField
          label="Write Value"
          type="number"
          size="small"
          value={value}
          onChange={(event) => setValue(event.target.value)}
          helperText={range}
          disabled={saving}
          inputProps={{ min: point.min ?? undefined, max: point.max ?? undefined, step: "any" }}
        />
        <Button variant="contained" size="small" onClick={handleSet} disabled={saving}>
          Set
        </Button>
        <Button size="small" onClick={handleClear} disabled={saving}>
          Clear Override
        </Button>
      </Box>
      {feedback && (
        <Alert severity={feedback.severity} sx={{ py: 0 }}>
          {feedback.message}
        </Alert>
      )}
    </Box>
  );
};

export const PointDialog = ({ onClose, run }) => {
  const [expanded, setExpanded] = useState(false);
  const [points, setPoints] = useState();
  const [runInfo, setRunInfo] = useState(run);
  const [stepping, setStepping] = useState(false);
  const [stepError, setStepError] = useState(null);

  const fetchPoints = async () => {
    const { payload: points } = await ky(`/api/v2/runs/${run.id}/points`).json();
    const { payload: values } = await ky(`/api/v2/runs/${run.id}/points/values`).json();
    for (const i in points) {
      const point = points[i];
      if (point.id in values) {
        point.value = values[point.id];
      }
    }
    setPoints(points);
  };

  const fetchRunInfo = async () => {
    const { payload } = await ky(`/api/v2/runs/${run.id}`).json();
    setRunInfo(payload);
  };

  useEffect(() => {
    fetchPoints().catch((err) => {
      console.error("Failed to load points:", err);
      setStepError("Failed to load points");
    });
  }, [run.id]);

  const handleChange = (pointId) => (event, expanded) => {
    setExpanded(expanded ? pointId : false);
  };

  const handleStep = async () => {
    setStepping(true);
    setStepError(null);
    try {
      await ky.post(`/api/v2/runs/${run.id}/advance`);
      await Promise.all([fetchRunInfo(), fetchPoints()]);
    } catch (err) {
      const body = await err.response?.json().catch(() => null);
      setStepError(body?.message || "Failed to step the simulation");
    } finally {
      setStepping(false);
    }
  };

  const collator = new Intl.Collator(undefined, { numeric: true, sensitivity: "base" });
  const sortPoints = (a, b) => collator.compare(a.name || a.id, b.name || b.id);

  const stepControls = () => {
    if (runInfo.status !== "RUNNING") return null;

    if (!runInfo.externalClock) {
      return (
        <Box sx={{ mb: 2 }}>
          <Typography variant="body2" color="textSecondary">
            Sim Time: {runInfo.datetime} &mdash; this run advances on its own (internal/realtime clock).
          </Typography>
        </Box>
      );
    }

    return (
      <Box sx={{ mb: 2 }}>
        <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
          <Typography variant="body2" color="textSecondary">
            Sim Time: {runInfo.datetime}
          </Typography>
          <Button variant="contained" size="small" onClick={handleStep} disabled={stepping}>
            {stepping ? "Stepping\u2026" : "Step Simulation"}
          </Button>
        </Box>
        <Typography variant="caption" color="textSecondary">
          This run uses an external clock: set input values above, then click Step Simulation to advance one timestep
          and read the resulting outputs.
        </Typography>
        {stepError && (
          <Alert severity="error" sx={{ mt: 1 }}>
            {stepError}
          </Alert>
        )}
      </Box>
    );
  };

  const table = () => {
    if (!points) {
      return (
        <Grid container justifyContent="center" alignItems="center">
          <Grid item>
            <CircularProgress />
          </Grid>
        </Grid>
      );
    } else {
      return (
        <div style={{ paddingTop: "2px" }}>
          {!points.length ? (
            <Typography align="center">— No points associated with run —</Typography>
          ) : (
            points.sort(sortPoints).map((point, i) => {
              return (
                <Accordion key={i} expanded={expanded === i} onChange={handleChange(i)}>
                  <AccordionSummary expandIcon={<ExpandMore />}>
                    <Typography>{point.name || point.id}</Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Table>
                      <TableHead>
                        <TableRow>
                          <TableCell style={{ fontWeight: "bold" }}>Key</TableCell>
                          <TableCell style={{ fontWeight: "bold" }}>Value</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {Object.entries(point).map(([key, value]) => {
                          return (
                            <TableRow key={key}>
                              <TableCell>{key}</TableCell>
                              <TableCell>{value}</TableCell>
                            </TableRow>
                          );
                        })}
                      </TableBody>
                    </Table>
                    {WRITABLE_TYPES.includes(point.type) && <PointWriteControl run={run} point={point} />}
                  </AccordionDetails>
                </Accordion>
              );
            })
          )}
        </div>
      );
    }
  };

  return (
    <div>
      <Dialog fullWidth={true} maxWidth="lg" open={true} onClose={onClose}>
        <DialogTitle>
          <Grid container justifyContent="space-between" alignItems="center">
            <span>{`${run.name} Points`}</span>
            <IconButton onClick={onClose}>
              <Close />
            </IconButton>
          </Grid>
        </DialogTitle>
        <DialogContent>
          {stepControls()}
          {table()}
        </DialogContent>
      </Dialog>
    </div>
  );
};
