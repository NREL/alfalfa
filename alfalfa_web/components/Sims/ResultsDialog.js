import React from "react";
import { Close } from "@mui/icons-material";
import {
  Dialog,
  DialogContent,
  DialogTitle,
  Grid,
  IconButton,
  List,
  ListItem,
  ListItemText,
  Typography
} from "@mui/material";

export const ResultsDialog = ({ onClose, sim }) => {
  const formatResults = (results) => {
    if (!results) {
      return <></>;
    }
    return Object.entries(results).map(([key, value]) => {
      if (key === "energy") {
        key += " [kWh]";
      } else if (key === "comfort") {
        key += " [K-h]";
      }
      return (
        <ListItem>
          <ListItemText primary={key} secondary={value.toFixed(3)} />
        </ListItem>
      );
    });
  };

  return (
    <Dialog fullWidth={true} maxWidth="lg" open={true} onClose={onClose}>
      <DialogTitle>
        <Grid container justifyContent="space-between" alignItems="center">
          <span>{`${sim.name} Results`}</span>
          <IconButton onClick={onClose}>
            <Close />
          </IconButton>
        </Grid>
      </DialogTitle>
      <DialogContent>
        {!Object.keys(sim.results).length ? (
          <Typography align="center">— No results associated with simulation —</Typography>
        ) : (
          <List>{formatResults(sim.results)}</List>
        )}
      </DialogContent>
    </Dialog>
  );
};
