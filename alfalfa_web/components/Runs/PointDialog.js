import React, { useEffect, useState } from "react";
import { Close, ExpandMore } from "@mui/icons-material";
import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
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
  Typography
} from "@mui/material";
import ky from "ky";

export const PointDialog = ({ onClose, run }) => {
  const [expanded, setExpanded] = useState(false);
  const [points, setPoints] = useState();

  useEffect(async () => {
    const { payload: points } = await ky(`/api/v2/runs/${run.id}/points`).json();
    await ky(`/api/v2/runs/${run.id}/points/values`)
      .json()
      .then(({ payload: values }) => {
        for (const i in points) {
          const point = points[i];
          if (point.id in values) {
            point.value = values[point.id];
          }
        }
        setPoints(points);
      });
  }, []);

  const handleChange = (pointId) => (event, expanded) => {
    setExpanded(expanded ? pointId : false);
  };

  const collator = new Intl.Collator(undefined, { numeric: true, sensitivity: "base" });
  const sortPoints = (a, b) => collator.compare(a.name || a.id, b.name || b.id);

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
        <DialogContent>{table()}</DialogContent>
      </Dialog>
    </div>
  );
};
