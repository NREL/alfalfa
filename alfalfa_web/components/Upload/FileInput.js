import React, { useRef, useState } from "react";
import { Button, CircularProgress, Typography } from "@mui/material";
import JSZip from "jszip";
import styles from "./Upload.scss";

export const FileInput = ({ onFileChange, disabled = false }) => {
  const [file, setFile] = useState(null);
  const [zipping, setZipping] = useState(false);
  const fileInputRef = useRef(null);
  const folderInputRef = useRef(null);

  const handleFileChange = (event) => {
    if (event.target.files.length) {
      const [file] = event.target.files;
      onFileChange(file);
      setFile(file);
    }
  };

  const handleFolderChange = async (event) => {
    const files = Array.from(event.target.files);
    if (!files.length) return;

    // webkitRelativePath looks like "<folderName>/<...>"; strip the folder
    // name itself so the zip's entries are relative to the folder's
    // contents (matching how models uploaded via the alfalfa-client are zipped).
    const folderName = files[0].webkitRelativePath.split("/")[0];

    setZipping(true);
    try {
      const zip = new JSZip();
      for (const entry of files) {
        const relativePath = entry.webkitRelativePath.slice(folderName.length + 1);
        zip.file(relativePath, entry);
      }
      const blob = await zip.generateAsync({ type: "blob" });
      const zipFile = new File([blob], `${folderName}.zip`, { type: "application/zip" });
      onFileChange(zipFile);
      setFile(zipFile);
    } finally {
      setZipping(false);
      event.target.value = "";
    }
  };

  const handleButtonClick = () => fileInputRef.current.click();

  const handleFolderButtonClick = () => folderInputRef.current.click();

  const busy = disabled || zipping;

  return (
    <div className={styles.fileInput}>
      <input className={styles.hidden} type="file" accept=".zip,.fmu" ref={fileInputRef} onInput={handleFileChange} />
      <input
        className={styles.hidden}
        type="file"
        ref={folderInputRef}
        onInput={handleFolderChange}
        webkitdirectory=""
        directory=""
        multiple
      />
      <div className={styles.fileName}>
        {zipping ? (
          <>
            <CircularProgress size={16} />
            <Typography variant="body1" color="textSecondary" component="span">
              Zipping folder&hellip;
            </Typography>
          </>
        ) : (
          <Typography
            variant="body1"
            component="span"
            color={file ? "textPrimary" : "textSecondary"}
            className={styles.fileNameText}>
            {file?.name ?? "No model selected"}
          </Typography>
        )}
      </div>
      <Button variant="outlined" color="primary" disabled={busy} onClick={handleButtonClick}>
        Select Model
      </Button>
      <Button variant="outlined" color="primary" disabled={busy} onClick={handleFolderButtonClick}>
        Select Folder
      </Button>
    </div>
  );
};
