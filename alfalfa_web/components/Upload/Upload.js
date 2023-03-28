import React, { useState } from "react";
import { Button, Grid, LinearProgress } from "@mui/material";
import ky from "ky";
import { FileInput } from "./FileInput";
import styles from "./Upload.scss";

export const Upload = () => {
  const [modelFile, setModelFile] = useState(null);
  const [uploading, setUploading] = useState(false);

  const onModelFileChange = (file) => {
    setModelFile(file);
    setUploading(false);
  };

  const uploadFile = async ({ fields, url }) => {
    const formData = new FormData();
    for (const [key, value] of Object.entries(fields)) {
      formData.append(key, value);
    }
    formData.append("file", modelFile);
    await ky.post(url, { body: formData });
  };

  const createRun = async ({ modelID }) => {
    await ky.post(`/api/v2/models/${modelID}/createRun`).json();
  };

  const upload = async () => {
    try {
      setUploading(true);
      const uploadData = await ky
        .post("/api/v2/models/upload", {
          json: {
            modelName: modelFile.name
          }
        })
        .json();
      await uploadFile(uploadData);
      await createRun(uploadData);
    } catch (err) {
      console.error("Upload failed:", err);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className={styles.root}>
      <LinearProgress variant={uploading ? "indeterminate" : "determinate"} value={0} />
      <div className={styles.center}>
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <FileInput onFileChange={onModelFileChange} />
          </Grid>
          <Grid item xs>
            <Button
              disabled={!/\.(fmu|zip)$/.test(modelFile?.name)}
              fullWidth={true}
              variant="contained"
              color="primary"
              onClick={upload}>
              Upload Model
            </Button>
          </Grid>
        </Grid>
      </div>
    </div>
  );
};
