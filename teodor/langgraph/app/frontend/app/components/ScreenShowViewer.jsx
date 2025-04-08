'use client';

import { useState } from 'react';
import { Box, Paper, Typography, IconButton, CircularProgress } from '@mui/material';
import { ZoomIn, ZoomOut, Fullscreen, FullscreenExit } from '@mui/icons-material';

export default function ScreenshotViewer({ screenshot, isLoading, title, bboxes = [] }) {
  const [zoom, setZoom] = useState(1);
  const [fullscreen, setFullscreen] = useState(false);

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '400px', bgcolor: 'grey.100', borderRadius: 1 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (!screenshot) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '400px', bgcolor: 'grey.100', borderRadius: 1 }}>
        <Typography color="text.secondary">No screenshot available</Typography>
      </Box>
    );
  }

  return (
    <Paper 
      elevation={3}
      sx={{ 
        position: fullscreen ? 'fixed' : 'relative',
        top: fullscreen ? 0 : 'auto',
        left: fullscreen ? 0 : 'auto',
        right: fullscreen ? 0 : 'auto',
        bottom: fullscreen ? 0 : 'auto',
        width: fullscreen ? '100vw' : '100%',
        height: fullscreen ? '100vh' : 'auto',
        maxHeight: fullscreen ? '100vh' : '600px',
        overflow: 'auto',
        display: 'flex',
        flexDirection: 'column',
        zIndex: fullscreen ? 1300 : 'auto',
      }}
    >
      <Box sx={{ p: 1, display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid', borderColor: 'divider', bgcolor: 'background.paper', position: 'sticky', top: 0, zIndex: 10 }}>
        <Typography variant="subtitle1">{title || 'Browser View'}</Typography>
        <Box>
          <IconButton onClick={() => setZoom(z => Math.max(0.5, z - 0.1))}>
            <ZoomOut />
          </IconButton>
          <Typography component="span" sx={{ mx: 1 }}>
            {Math.round(zoom * 100)}%
          </Typography>
          <IconButton onClick={() => setZoom(z => Math.min(2, z + 0.1))}>
            <ZoomIn />
          </IconButton>
          <IconButton onClick={() => setFullscreen(!fullscreen)}>
            {fullscreen ? <FullscreenExit /> : <Fullscreen />}
          </IconButton>
        </Box>
      </Box>

      <Box sx={{ overflow: 'auto', flex: 1, p: 2, display: 'flex', justifyContent: 'center' }}>
        <Box sx={{ position: 'relative', transform: `scale(${zoom})`, transformOrigin: 'top center', transition: 'transform 0.2s ease' }}>
          <img 
            src={`data:image/png;base64,${screenshot}`}
            alt="Browser screenshot"
            style={{ maxWidth: '100%', boxShadow: '0 4px 8px rgba(0,0,0,0.1)' }}
          />
          
          {bboxes && bboxes.map((bbox, index) => (
            <div 
              key={index}
              style={{
                position: 'absolute',
                left: `${bbox.x}px`,
                top: `${bbox.y}px`,
                width: '0px',
                height: '0px',
                outline: '2px dashed',
                outlineColor: `hsl(${index * 137.5 % 360}, 70%, 50%)`,
                pointerEvents: 'none',
                zIndex: 2,
                transform: 'translate(-50%, -50%)'
              }}
            >
              <span style={{
                position: 'absolute',
                top: '-19px',
                left: '0px',
                background: `hsl(${index * 137.5 % 360}, 70%, 50%)`,
                color: 'white',
                padding: '2px 4px',
                fontSize: '12px',
                borderRadius: '2px'
              }}>
                {index}
              </span>
            </div>
          ))}
        </Box>
      </Box>
    </Paper>
  );
}