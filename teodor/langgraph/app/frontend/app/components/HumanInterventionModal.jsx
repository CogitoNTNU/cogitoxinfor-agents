'use client';

import { useState } from 'react';
import { Dialog, DialogTitle, DialogContent, DialogActions, Button, TextField, Typography, Box } from '@mui/material';

export default function InterventionModal({ open, onClose, interventionData, onRespond }) {
  const [response, setResponse] = useState('');
  
  const handleSubmit = () => {
    // Important: Send a string (empty string for approval)
    onRespond(response || '');
    setResponse('');
  };

  if (!interventionData) return null;
  
  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>Agent Requesting Assistance</DialogTitle>
      
      <DialogContent>
        <Typography variant="subtitle1" gutterBottom>
          The agent needs your help with the following:
        </Typography>
        
        <Typography variant="body1" sx={{ bgcolor: 'grey.100', p: 2, borderRadius: 1, my: 2 }}>
          {interventionData.message}
        </Typography>
        
        {interventionData.screenshot && (
          <Box sx={{ my: 3 }}>
            <Typography variant="subtitle2" gutterBottom>
              Current Browser View:
            </Typography>
            <img 
              src={`data:image/png;base64,${interventionData.screenshot}`}
              alt="Current browser state"
              style={{ maxWidth: '100%', maxHeight: '300px', objectFit: 'contain', border: '1px solid #ddd' }}
            />
          </Box>
        )}
        
        <TextField
          fullWidth
          multiline
          rows={3}
          label="Your response or instructions"
          value={response}
          onChange={(e) => setResponse(e.target.value)}
          placeholder="Leave empty to approve the action"
          variant="outlined"
          sx={{ mt: 2 }}
        />
        
        <Typography variant="caption" sx={{ display: 'block', mt: 1, color: 'text.secondary' }}>
          Leave blank to approve the agent's action.
        </Typography>
      </DialogContent>
      
      <DialogActions>
        <Button onClick={onClose} color="inherit">Cancel</Button>
        <Button onClick={handleSubmit} variant="contained" color="primary">
          Submit Response
        </Button>
      </DialogActions>
    </Dialog>
  );
}