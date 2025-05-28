import React from 'react';
import { Box, Typography } from '@mui/material';

const ObjectivePlot = () => {
  return (
    <Box sx={{ p: 2 }}>
      <Typography variant="subtitle1">Objective Plot</Typography>
      {/* Optional: Show static image or message */}
      <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
        Objective plot is now controlled via the sidebar.
      </Typography>
    </Box>
  );
};

export default ObjectivePlot;