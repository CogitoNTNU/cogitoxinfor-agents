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

const AVAILABLE_ACTIONS = [
  'NAVIGATE',
  'CLICK',
  'TYPE',
  'WAIT',
  'SCROLL'
];

const AgentController = ({ onStart, onStop, isRunning }) => {
  const [activeTab, setActiveTab] = useState(0);
  const [query, setQuery] = useState('');
  const [testActions, setTestActions] = useState([]);
  const [humanIntervention, setHumanIntervention] = useState(true);

  const handleAddAction = () => {
    setTestActions([...testActions, { action: AVAILABLE_ACTIONS[0], args: '' }]);
  };

  const handleRemoveAction = (index) => {
    setTestActions(testActions.filter((_, i) => i !== index));
  };

  const handleActionChange = (index, field, value) => {
    const updatedActions = [...testActions];
    updatedActions[index] = { ...updatedActions[index], [field]: value };
    setTestActions(updatedActions);
  };

  const handleStart = () => {
    const payload = {
      testing: activeTab === 1,
      human_intervention: humanIntervention,
      query: activeTab === 0 ? query : '',
      test_actions: activeTab === 1 ? testActions : []
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
              onClick={handleAddAction}
              sx={{ mb: 2 }}
            >
              Add Action
            </Button>
            
            {testActions.map((action, index) => (
              <Paper
                key={index}
                sx={{ p: 2, mb: 1, display: 'flex', alignItems: 'center', gap: 2 }}
              >
                <Select
                  size="small"
                  value={action.action}
                  onChange={(e) => handleActionChange(index, 'action', e.target.value)}
                  sx={{ width: 120 }}
                >
                  {AVAILABLE_ACTIONS.map(act => (
                    <MenuItem key={act} value={act}>{act}</MenuItem>
                  ))}
                </Select>
                <TextField
                  size="small"
                  label="Arguments"
                  value={action.args}
                  onChange={(e) => handleActionChange(index, 'args', e.target.value)}
                  sx={{ flex: 1 }}
                />
                <IconButton onClick={() => handleRemoveAction(index)} color="error">
                  <DeleteIcon />
                </IconButton>
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
          disabled={activeTab === 0 && !query.trim()}
        >
          {isRunning ? "Stop Agent" : "Start Agent"}
        </Button>
      </CardContent>
    </Card>
  );
};

export default AgentController;