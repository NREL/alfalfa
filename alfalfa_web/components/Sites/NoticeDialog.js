import React from "react";
import { Close } from "@mui/icons-material";
import { Dialog, DialogContent, DialogTitle, Grid, IconButton } from "@mui/material";

export const NoticeDialog = ({ onClose, run }) => {
  const notices = run.notices || [];
  return (
    <div>
      <Dialog fullWidth={true} maxWidth="lg" open={true} onClose={onClose}>
        <DialogTitle>
          <Grid container justifyContent="space-between" alignItems="center">
            <span>{`${run.name} Notices`}</span>
            <IconButton onClick={onClose}>
              <Close />
            </IconButton>
          </Grid>
        </DialogTitle>
        <DialogContent>
          {notices.map((notice, index) => (
            <pre key={index} style={{ whiteSpace: "pre-wrap" }}>
              {notice}
            </pre>
          ))}
        </DialogContent>
      </Dialog>
    </div>
  );
};
