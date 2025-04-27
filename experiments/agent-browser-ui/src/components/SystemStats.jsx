import React from 'react';
import { Box, Typography, Grid, Paper } from '@mui/material';

function SystemStats({ stats }) {
  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        System Statistics
      </Typography>
      
      <Grid container spacing={2}>
        <Grid item xs={12} sm={4}>
          <Paper sx={{ p: 2, textAlign: 'center', bgcolor: '#f5f5f5' }}>
            <Typography variant="subtitle2">Total Agents</Typography>
            <Typography variant="h4">{stats.total_agents || 0}</Typography>
          </Paper>
        </Grid>
        
        <Grid item xs={12} sm={4}>
          <Paper sx={{ p: 2, textAlign: 'center', bgcolor: '#f5f5f5' }}>
            <Typography variant="subtitle2">Memory Usage</Typography>
            <Typography variant="h4">
              {stats.memory_usage_mb ? `${stats.memory_usage_mb.toFixed(2)} MB` : 'N/A'}
            </Typography>
          </Paper>
        </Grid>
        
        <Grid item xs={12} sm={4}>
          <Paper sx={{ p: 2, textAlign: 'center', bgcolor: '#f5f5f5' }}>
            <Typography variant="subtitle2">CPU Usage</Typography>
            <Typography variant="h4">
              {stats.cpu_percent ? `${stats.cpu_percent.toFixed(2)}%` : 'N/A'}
            </Typography>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
}

export default SystemStats;