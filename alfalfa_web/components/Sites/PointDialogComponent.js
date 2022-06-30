import { ExpandMore } from "@mui/icons-material";
import {
  AccordionDetails,
  CircularProgress,
  Dialog,
  DialogContent,
  DialogTitle,
  Grid,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography
} from "@mui/material";
import React, { useState } from "react";

function PointDialogComponent(props) {
  //handleRequestClose = () => {
  //  this.props.onClosePointsClick();
  //}

  const [expanded, setExpanded] = useState(null);

  const handleChange = (pointId) => (event, expanded) => {
    setExpanded(expanded ? pointId : false);
  };

  const table = () => {
    if (props.data.networkStatus === 1) {
      // 1 for loading https://www.apollographql.com/docs/react/api/react-apollo.html#graphql-query-data-networkStatus
      return (
        <Grid container justifyContent="center" alignItems="center">
          <Grid item>
            <CircularProgress />
          </Grid>
        </Grid>
      );
    } else {
      const points = props.data.viewer.sites[0].points;
      return (
        <div>
          {points.map((point, i) => {
            return (
              <Accordion key={i} expanded={expanded === i} onChange={handleChange(i)}>
                <AccordionSummary expandIcon={<ExpandMore />}>
                  <Typography>{point.dis}</Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Key</TableCell>
                        <TableCell>Value</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {point.tags.map((tag) => {
                        return (
                          <TableRow key={tag.key}>
                            <TableCell>{tag.key}</TableCell>
                            <TableCell>{tag.value}</TableCell>
                          </TableRow>
                        );
                      })}
                    </TableBody>
                  </Table>
                </AccordionDetails>
              </Accordion>
            );
          })}
        </div>
      );
    }
  };

  if (props.site) {
    return (
      <div>
        <Dialog fullWidth={true} maxWidth="lg" open={true} onBackdropClick={props.onBackdropClick}>
          <DialogTitle>{props.site.name + " Points"}</DialogTitle>
          <DialogContent>{table()}</DialogContent>
        </Dialog>
      </div>
    );
  } else {
    return <div />;
  }
}

export default PointDialogComponent;
