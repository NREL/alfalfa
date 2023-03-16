import React from "react";
import { Close } from "@mui/icons-material";
import { Dialog, DialogContent, DialogTitle, Grid, IconButton } from "@mui/material";

export const ErrorDialog = ({ onClose, site }) => {
  return (
    <div>
      <Dialog fullWidth={true} maxWidth="lg" open={true} onClose={onClose}>
        <DialogTitle>
          <Grid container justifyContent="space-between" alignItems="center">
            <span>{`${site.name} Error Log`}</span>
            <IconButton onClick={onClose}>
              <Close />
            </IconButton>
          </Grid>
        </DialogTitle>
        <DialogContent>
          <pre style={{ whiteSpace: "pre-wrap" }}>{site.errorLog}</pre>
        </DialogContent>
      </Dialog>
    </div>
  );
};
