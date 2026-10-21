import React, { useState } from "react";
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  Grid,
  LinearProgress,
  Snackbar,
  Typography
} from "@mui/material";
import ky from "ky";
import { useNavigate } from "react-router-dom";
import { FileInput } from "./FileInput";
import styles from "./Upload.scss";

const STATUS = {
  IDLE: "idle",
  UPLOADING: "uploading",
  PROCESSING: "processing"
};

const STATUS_MESSAGE = {
  [STATUS.UPLOADING]: "Uploading model\u2026",
  [STATUS.PROCESSING]: "Processing model\u2026 this can take a while for OSM models"
};

export const Upload = () => {
  const navigate = useNavigate();
  const [resetKey, setResetKey] = useState(0);
  const [modelFile, setModelFile] = useState(null);
  const [status, setStatus] = useState(STATUS.IDLE);
  const [errorMessage, setErrorMessage] = useState(null);
  const [showCompleteDialog, setShowCompleteDialog] = useState(false);
  const busy = status === STATUS.UPLOADING || status === STATUS.PROCESSING;

  const onModelFileChange = (file) => {
    setModelFile(file);
    setStatus(STATUS.IDLE);
  };

  const uploadFile = async ({ fields, url }) => {
    const formData = new FormData();
    for (const [key, value] of Object.entries(fields)) {
      formData.append(key, value);
    }
    formData.append("file", modelFile);
    await ky.post(url, { body: formData });
  };

  const createRun = async ({ modelId }) => {
    await ky.post(`/api/v2/models/${modelId}/createRun`).json();
  };

  const closeErrorToast = (event, reason) => {
    if (reason === "clickaway") return;
    setErrorMessage(null);
  };

  const upload = async () => {
    const fileName = modelFile.name;
    try {
      setStatus(STATUS.UPLOADING);
      const { payload } = await ky
        .post("/api/v2/models/upload", {
          json: {
            modelName: fileName
          }
        })
        .json();
      await uploadFile(payload);
      setStatus(STATUS.PROCESSING);
      await createRun(payload);
      setStatus(STATUS.IDLE);
      setShowCompleteDialog(true);
    } catch (err) {
      console.error("Upload failed:", err);
      setStatus(STATUS.IDLE);
      setErrorMessage(`Upload of ${fileName} failed. Please try again.`);
    }
  };

  const uploadAnother = () => {
    setShowCompleteDialog(false);
    setModelFile(null);
    setResetKey((key) => key + 1);
  };

  const goToSites = () => {
    setShowCompleteDialog(false);
    navigate("/sites");
  };

  return (
    <div className={styles.root}>
      <LinearProgress variant={busy ? "indeterminate" : "determinate"} value={0} />
      <div className={styles.center}>
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <Typography variant="h5" gutterBottom>
              Upload a Model
            </Typography>
            <Typography variant="body1" color="textSecondary">
              Select an OpenStudio model (zipped .osm) or FMU (.fmu) and upload it to add it as a new run &mdash; or use
              &ldquo;Select Folder&rdquo; to pick an unzipped OpenStudio model folder directly and it will be zipped
              automatically. Alfalfa will process the model &mdash; this can take a few minutes, especially for OSM
              models. Once uploaded, go to the &ldquo;Sites&rdquo; page to start and control the run.
            </Typography>
          </Grid>
          <Grid item xs={12}>
            <FileInput key={resetKey} onFileChange={onModelFileChange} disabled={busy} />
          </Grid>
          <Grid item xs={12}>
            <Button
              disabled={busy || !/\.(fmu|zip)$/.test(modelFile?.name)}
              fullWidth={true}
              variant="contained"
              color="primary"
              onClick={upload}>
              Upload Model
            </Button>
          </Grid>
          {busy && (
            <Grid item xs={12}>
              <Box className={styles.status}>
                <CircularProgress size={24} />
                <Typography variant="body2">{STATUS_MESSAGE[status]}</Typography>
              </Box>
            </Grid>
          )}
        </Grid>
      </div>
      <Dialog open={showCompleteDialog} onClose={uploadAnother}>
        <DialogTitle>Upload Complete</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Your model has been uploaded and added as a new run. Would you like to upload another model, or go to the
            Sites page to start it?
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={uploadAnother}>Upload Another</Button>
          <Button onClick={goToSites} variant="contained" color="primary">
            Go to Sites
          </Button>
        </DialogActions>
      </Dialog>
      <Snackbar
        open={!!errorMessage}
        autoHideDuration={null}
        onClose={closeErrorToast}
        anchorOrigin={{ vertical: "bottom", horizontal: "center" }}>
        <Alert onClose={() => setErrorMessage(null)} severity="error" variant="filled" sx={{ width: "100%" }}>
          {errorMessage}
        </Alert>
      </Snackbar>
    </div>
  );
};
