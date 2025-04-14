import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Tabs,
  Tab,
  TextField,
  Button,
  Select,
  MenuItem,
  IconButton,
  Switch,
  FormControlLabel,
  Typography,
  Paper
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import StopIcon from '@mui/icons-material/Stop';
import InfoIcon from '@mui/icons-material/Info';
import Tooltip from '@mui/material/Tooltip';


const TOOL_CONFIGURATIONS = {
  NAVIGATE: {
    args: 1,
    validator: (args) => {
      const url = args[0];
      return {
        isValid: url && typeof url === 'string',
        error: 'URL must be a non-empty string'
      };
    },
    placeholder: 'Enter URL (e.g., https://www.google.com)'
  },
  CLICK: {
    args: 1,
    validator: (args) => {
      const id = args[0];
      return {
        isValid: !isNaN(parseInt(id)),
        error: 'Element ID must be a number'
      };
    },
    placeholder: 'Enter element ID (e.g., 6)'
  },
  TYPE: {
    args: 2,
    validator: (args) => {
      const [id, text] = args;
      return {
        isValid: !isNaN(parseInt(id)) && typeof text === 'string' && text.length > 0,
        error: 'Requires element ID (number) and text to type'
      };
    },
    placeholder: 'Enter element ID, text (e.g., 6, search text)'
  },
  WAIT: {
    args: 1,
    validator: (args) => {
      const seconds = args[0];
      return {
        isValid: !isNaN(parseInt(seconds)) && parseInt(seconds) > 0,
        error: 'Wait time must be a positive number'
      };
    },
    placeholder: 'Enter seconds to wait (e.g., 2)'
  },
  SCROLL: {
    args: 2,
    validator: (args) => {
      const [target, direction] = args;
      const validDirections = ['up', 'down'];
      const isValidTarget = target.toUpperCase() === 'WINDOW' || !isNaN(parseInt(target));
      return {
        isValid: isValidTarget && validDirections.includes(direction.toLowerCase()),
        error: 'Target must be "WINDOW" or element ID, direction must be "up" or "down"'
      };
    },
    placeholder: 'Enter target (WINDOW or ID), direction (up/down)'
  }
};

const formatArguments = (value, action, isBackspace = false) => {
  const config = TOOL_CONFIGURATIONS[action];
  const values = value.split(',').map(v => v.trim()).filter(v => v !== '');
  
  // Handle backspace logic
  if (isBackspace) {
    // If text contains comma without proper spacing
    if (value.match(/,\S/)) {
      return value.slice(0, -1);
    }
    
    // If ending with comma and space
    if (value.endsWith(', ')) {
      return value.slice(0, -2);
    }
    
    // If ending with just comma
    if (value.endsWith(',')) {
      return '';  // Clear everything when the last comma is hit
    }
    
    // If we have a single value (no commas)
    if (!value.includes(',')) {
      return value.slice(0, -1);
    }
    
    // If we have multiple values, handle the last one
    const lastCommaIndex = value.lastIndexOf(',');
    if (lastCommaIndex !== -1) {
      const beforeComma = value.slice(0, lastCommaIndex + 2); // Keep comma and space
      const afterComma = value.slice(lastCommaIndex + 2);
      if (!afterComma.trim()) {
        return value.slice(0, lastCommaIndex);
      }
      return beforeComma + afterComma.slice(0, -1);
    }
  }

  return value;  // Return unmodified value for non-backspace operations
};


const AgentController = ({ onStart, onStop, isRunning }) => {
  const [activeTab, setActiveTab] = useState(0);
  const [query, setQuery] = useState('');
  const [testActions, setTestActions] = useState([]);
  const [humanIntervention, setHumanIntervention] = useState(true);
  const [errors, setErrors] = useState({});

  const parseArguments = (argsString, action) => {
    const args = argsString.split(',').map(arg => arg.trim());
    if (args.length !== TOOL_CONFIGURATIONS[action].args) {
      return null;
    }
    return args;
  };

  const validateAction = (action, argsString) => {
    const config = TOOL_CONFIGURATIONS[action];
    const args = parseArguments(argsString, action);
    
    if (!args) {
      return {
        isValid: false,
        error: `Expected ${config.args} argument(s)`
      };
    }
    
    return config.validator(args);
  };

  const handleActionChange = (index, field, value) => {
    const updatedActions = [...testActions];
    const action = field === 'action' ? value : updatedActions[index].action;
    const args = field === 'args' ? value : updatedActions[index].args;
    
    updatedActions[index] = { ...updatedActions[index], [field]: value };
    setTestActions(updatedActions);

    // Validate the updated action
    const validation = validateAction(action, args);
    setErrors(prev => ({
      ...prev,
      [index]: validation.error
    }));
  };

  const handleStart = () => {
    // Validate all actions before starting
    const hasErrors = testActions.some((action, index) => {
      const validation = validateAction(action.action, action.args);
      return !validation.isValid;
    });

    if (hasErrors) {
      return; // Don't start if there are validation errors
    }

    const formattedActions = testActions.map(action => {
      const args = parseArguments(action.args, action.action);
      return [action.action, args];
    });

    const payload = {
      testing: activeTab === 1,
      human_intervention: humanIntervention,
      query: activeTab === 0 ? query : '',
      test_actions: formattedActions
    };
    onStart(payload);
  };

  return (
    <Card sx={{ mb: 3 }}>
      <CardContent>
        <Tabs
          value={activeTab}
          onChange={(_, newValue) => setActiveTab(newValue)}
          sx={{ mb: 2 }}
        >
          <Tab label="Agent Mode" />
          <Tab label="Test Mode" />
        </Tabs>

        <FormControlLabel
          control={
            <Switch
              checked={humanIntervention}
              onChange={(e) => setHumanIntervention(e.target.checked)}
            />
          }
          label="Human Intervention"
          sx={{ mb: 2 }}
        />

        {activeTab === 0 ? (
          <TextField
            fullWidth
            multiline
            rows={4}
            label="Query"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            sx={{ mb: 2 }}
          />
        ) : (
            <Box sx={{ mb: 2 }}>
            <Button
              startIcon={<AddIcon />}
              variant="outlined"
              onClick={() => setTestActions([...testActions, { action: 'NAVIGATE', args: '' }])}
              sx={{ mb: 2 }}
            >
              Add Action
            </Button>
            
            {testActions.map((action, index) => (
              <Paper
                key={index}
                sx={{ p: 2, mb: 1, display: 'flex', flexDirection: 'column', gap: 1 }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <Select
                    size="small"
                    value={action.action}
                    onChange={(e) => handleActionChange(index, 'action', e.target.value)}
                    sx={{ width: 120 }}
                  >
                    {Object.keys(TOOL_CONFIGURATIONS).map(act => (
                      <MenuItem key={act} value={act}>{act}</MenuItem>
                    ))}
                  </Select>
                  <Box sx={{ display: 'flex', alignItems: 'center', flex: 1 }}>
                  <TextField
                      size="small"
                      label="Arguments"
                      value={action.args}
                      onChange={(e) => {
                        let value = e.target.value;
                        // If user hits space and we don't already have a comma
                        if (value.endsWith(' ') && !value.includes(',')) {
                          // Replace the space with a comma and space
                          value = value.trim() + ', ';
                        }
                        const formattedValue = formatArguments(value, action.action);
                        handleActionChange(index, 'args', formattedValue);
                      }}
                      onKeyDown={(e) => {
                        if (e.key === 'Backspace' && action.args) {
                          e.preventDefault();
                          const formattedValue = formatArguments(action.args, action.action, true);
                          handleActionChange(index, 'args', formattedValue);
                        }
                      }}
                        placeholder={TOOL_CONFIGURATIONS[action.action].placeholder}
                        error={Boolean(errors[index])}
                        helperText={errors[index]}
                        InputProps={{
                          sx: {
                            '&::placeholder': {
                              fontSize: '0.75rem',
                              fontStyle: 'italic'
                            }
                          }
                        }}
                        FormHelperTextProps={{
                          sx: {
                            fontSize: '0.75rem'
                          }
                        }}
                        sx={{ 
                          flex: 1,
                          '& .MuiInputBase-input::placeholder': {
                            fontSize: '0.75rem',
                            opacity: 0.7
                          }
                        }}
                      />
                    <Tooltip 
                      title={
                        <div>
                          <Typography variant="caption" display="block">
                            Format: {TOOL_CONFIGURATIONS[action.action].placeholder}
                          </Typography>
                          <Typography variant="caption" display="block">
                            Required Arguments: {TOOL_CONFIGURATIONS[action.action].args}
                          </Typography>
                        </div>
                      }
                      placement="top"
                    >
                      <IconButton size="small" sx={{ ml: 1 }}>
                        <InfoIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </Box>
                  <IconButton onClick={() => {
                    const newActions = testActions.filter((_, i) => i !== index);
                    setTestActions(newActions);
                    const newErrors = {...errors};
                    delete newErrors[index];
                    setErrors(newErrors);
                  }} color="error">
                    <DeleteIcon />
                  </IconButton>
                </Box>
              </Paper>
            ))}
          </Box>
        )}

        <Button
          fullWidth
          variant="contained"
          color={isRunning ? "error" : "primary"}
          startIcon={isRunning ? <StopIcon /> : <PlayArrowIcon />}
          onClick={isRunning ? onStop : handleStart}
          disabled={
            (activeTab === 0 && !query.trim()) || 
            (activeTab === 1 && (testActions.length === 0 || Object.keys(errors).length > 0))
          }
        >
          {isRunning ? "Stop Agent" : "Start Agent"}
        </Button>
      </CardContent>
    </Card>
  );
};

export default AgentController;