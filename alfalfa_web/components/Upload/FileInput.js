import React, { useRef, useState } from "react";
import { TextField } from "@mui/material";
import styles from "./Upload.scss";

export const FileInput = ({ onFileChange }) => {
  const [file, setFile] = useState(null);
  const fileInputRef = useRef(null);

  const handleFileChange = (event) => {
    if (event.target.files.length) {
      const [file] = event.target.files;
      onFileChange(file);
      setFile(file);
    }
  };

  const handleTextInputClick = () => fileInputRef.current.click();

  return (
    <div>
      <input className={styles.hidden} type="file" accept=".zip,.fmu" ref={fileInputRef} onInput={handleFileChange} />
      <TextField
        fullWidth={true}
        label="Select Model"
        onClick={handleTextInputClick}
        value={file?.name ?? ""}
        inputProps={{
          readOnly: true,
          style: {
            cursor: "pointer"
          }
        }}
        InputLabelProps={{
          shrink: !!file
        }}
      />
    </div>
  );
};
