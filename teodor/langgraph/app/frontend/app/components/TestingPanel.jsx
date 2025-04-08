'use client';

import { useState } from 'react';
import { 
  Box, 
  Typography, 
  Switch, 
  FormControlLabel, 
  TextField, 
  Button,
  IconButton,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  FormControl,
  InputLabel,
  Select,
  MenuItem
} from '@mui/material';
import { Add as AddIcon, Remove as RemoveIcon, ExpandMore as ExpandMoreIcon } from '@mui/icons-material';

const DEFAULT_ACTION_TYPES = [
  "CLICK",
  "TYPE",
  "SCROLL",
  "WAIT",
  "NAVIGATE"
];

export default function TestingPanel({ 
  isTesting, 
  onTestingChange, 
  testActions, 
  onTestActionsChange,
  isHumanIntervention,
  onHumanInterventionChange
}) {
  // Add new test action
  const addTestAction = () => {
    const newAction = {
      type: "CLICK",
      args: ["0"]
    };
    onTestActionsChange([...testActions, newAction]);
  };
  
  // Remove test action by index
  const removeTestAction = (index) => {
    const updatedActions = [...testActions];
    updatedActions.splice(index, 1);
    onTestActionsChange(updatedActions);
  };
  
  // Update test action
  const updateTestAction = (index, field, value) => {
    const updatedActions = [...testActions];
    if (field === "type") {
      updatedActions[index].type = value;
    } else if (field === "args") {
      updatedActions[index].args = value.split(',').map(arg => arg.trim());
    }
    onTestActionsChange(updatedActions);
  };
  
  return (
    <Accordion>
      <AccordionSummary
        expandIcon={<ExpandMoreIcon />}
        aria-controls="testing-panel-content"
        id="testing-panel-header"
      >
        <Typography>Testing Settings</Typography>
      </AccordionSummary>
      <AccordionDetails>
        <Box sx={{ mb: 2 }}>
          <FormControlLabel 
            control={
              <Switch 
                checked={isTesting} 
                onChange={(e) => onTestingChange(e.target.checked)}
              />
            } 
            label="Enable Testing Mode" 
          />
        </Box>
        
        <Box sx={{ mb: 2 }}>
          <FormControlLabel 
            control={
              <Switch 
                checked={isHumanIntervention} 
                onChange={(e) => onHumanInterventionChange(e.target.checked)}
              />
            } 
            label="Enable Human Intervention" 
          />
        </Box>
        
        {isTesting && (
          <Box sx={{ mt: 2 }}>
            <Typography variant="subtitle2" gutterBottom>Test Actions</Typography>
            
            {testActions.map((action, index) => (
              <Box 
                key={index}
                sx={{ 
                  display: 'flex', 
                  alignItems: 'center',
                  gap: 2,
                  mb: 2
                }}
              >
                <Typography variant="body2" sx={{ minWidth: '30px' }}>{index + 1}.</Typography>
                
                <FormControl size="small" sx={{ minWidth: 120 }}>
                  <InputLabel>Action</InputLabel>
                  <Select
                    value={action.type}
                    label="Action"
                    onChange={(e) => updateTestAction(index, 'type', e.target.value)}
                  >
                    {DEFAULT_ACTION_TYPES.map(type => (
                      <MenuItem key={type} value={type}>{type}</MenuItem>
                    ))}
                  </Select>
                </FormControl>
                
                <TextField 
                  size="small"
                  label="Arguments" 
                  variant="outlined"
                  value={action.args.join(', ')}
                  onChange={(e) => updateTestAction(index, 'args', e.target.value)}
                  sx={{ flex: 1 }}
                  placeholder="e.g.: 0, text to type"
                />
                
                <IconButton 
                  color="error" 
                  onClick={() => removeTestAction(index)}
                >
                  <RemoveIcon />
                </IconButton>
              </Box>
            ))}
            
            <Button 
              startIcon={<AddIcon />}
              variant="outlined"
              size="small"
              onClick={addTestAction}
              sx={{ mt: 1 }}
            >
              Add Test Action
            </Button>
          </Box>
        )}
      </AccordionDetails>
    </Accordion>
  );
}