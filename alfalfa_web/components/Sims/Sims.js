import React, { useEffect, useState } from "react";
import { MoreVert } from "@mui/icons-material";
import { Button, Checkbox, Grid, IconButton, Table, TableBody, TableCell, TableHead, TableRow } from "@mui/material";
import ky from "ky";
import { DateTime } from "luxon";
import { ResultsDialog } from "./ResultsDialog";

export const Sims = () => {
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState([]);
  const [simulations, setSimulations] = useState([]);
  const [showResultsDialog, setShowResultsDialog] = useState(null);

  const fetchSimulations = async () => {
    const { data: simulations } = await ky("/api/v2/simulations").json();
    setSimulations(simulations);
    setLoading(false);
  };

  useEffect(() => {
    fetchSimulations();
    const id = setInterval(fetchSimulations, 1000);

    return () => clearInterval(id);
  }, []);

  const isSelected = (siteRef) => selected.includes(siteRef);

  const selectedSims = () => simulations.filter(({ id }) => selected.includes(id));

  const handleRowClick = (event, siteRef) => {
    const newSelected = selected.includes(siteRef) ? selected.filter((id) => id !== siteRef) : [...selected, siteRef];
    setSelected(newSelected);
  };

  const buttonsDisabled = () => selected.length === 0;

  const handleDownload = async () => {
    for (const { url } of selectedSims()) {
      if (url) location.href = url;
    }
  };

  const handleShowResults = (event, sim) => {
    event.stopPropagation();
    setShowResultsDialog(sim);
  };

  const handleCloseResults = () => setShowResultsDialog(null);

  if (loading) {
    return null;
  } else {
    return (
      <Grid container direction="column">
        {showResultsDialog && <ResultsDialog sim={showResultsDialog} onClose={handleCloseResults} />}
        <Grid item>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell padding="checkbox"></TableCell>
                <TableCell>Name</TableCell>
                <TableCell>Completed Time</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Results</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {simulations.map((sim) => {
                return (
                  <TableRow
                    key={sim.id}
                    style={{ cursor: "default" }}
                    onClick={(event) => handleRowClick(event, sim.id)}>
                    <TableCell padding="checkbox">
                      <Checkbox checked={isSelected(sim.id)} />
                    </TableCell>
                    <TableCell padding="none">{sim.name}</TableCell>
                    <TableCell>
                      <span title={sim.timeCompleted}>
                        {DateTime.fromISO(sim.timeCompleted).toFormat("LLLL dd y, h:mm a")}
                      </span>
                    </TableCell>
                    <TableCell padding="none">{sim.status.toUpperCase()}</TableCell>
                    <TableCell>
                      <IconButton onClick={(event) => handleShowResults(event, sim)}>
                        <MoreVert />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </Grid>
        <Grid item>
          <Grid container justifyContent="flex-start" alignItems="center" style={{ marginLeft: 0, paddingLeft: 16 }}>
            <Grid item>
              <Button variant="contained" disabled={buttonsDisabled()} onClick={handleDownload} sx={{ m: 1 }}>
                Download Test Results
              </Button>
            </Grid>
          </Grid>
        </Grid>
      </Grid>
    );
  }
};
