'use client';

import { useState, useEffect, useRef } from 'react';
import { Box, Paper, Typography, Tabs, Tab } from '@mui/material';
import { CodeRounded, ImageRounded } from '@mui/icons-material';

export default function DOMRenderer({ domData, screenshot, bboxes = [] }) {
  const [viewMode, setViewMode] = useState('rendered');
  const iframeRef = useRef(null);
  const [iframeLoaded, setIframeLoaded] = useState(false);

  useEffect(() => {
    if (!domData || !iframeRef.current) return;
    
    // Create a safe document with original styles but sanitized scripts
    const doc = iframeRef.current.contentDocument;
    if (!doc) return;
    
    try {
      // Create HTML with base URL to resolve relative paths
      const baseTag = domData.base_url ? 
        `<base href="${domData.base_url}">` : '';
      
      // Create style tag with extracted styles
      const styleTag = domData.styles ? 
        `<style id="extracted-styles">${domData.styles}</style>` : '';
      
      // Create HTML document with security measures
      const safeHtml = `
        <!DOCTYPE html>
        <html>
          <head>
            ${baseTag}
            <title>${domData.title || 'Page View'}</title>
            <meta http-equiv="Content-Security-Policy" 
                  content="default-src 'self' 'unsafe-inline' data:; 
                           img-src * data:; 
                           style-src 'self' 'unsafe-inline';">
            ${styleTag}
          </head>
          <body>
            ${domData.html.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')}
          </body>
        </html>
      `;
      
      doc.open();
      doc.write(safeHtml);
      doc.close();
      
      // Mark page elements with bounding boxes (similar to backend)
      if (bboxes && bboxes.length > 0) {
        doc.body.insertAdjacentHTML('beforeend', `
          <style>
            .bbox-overlay {
              position: absolute;
              outline: 2px dashed;
              pointer-events: none;
              z-index: 10000;
            }
            .bbox-label {
              position: absolute;
              top: -19px;
              left: 0;
              color: white;
              padding: 2px 4px;
              font-size: 12px;
              border-radius: 2px;
            }
          </style>
        `);
        
        bboxes.forEach((bbox, index) => {
          const color = `hsl(${(index * 137.5) % 360}, 70%, 50%)`;
          const div = doc.createElement('div');
          div.className = 'bbox-overlay';
          div.style.left = `${bbox.x - (bbox.width/2)}px`;
          div.style.top = `${bbox.y - (bbox.height/2)}px`;
          div.style.width = `${bbox.width}px`;
          div.style.height = `${bbox.height}px`;
          div.style.outlineColor = color;
          
          const label = doc.createElement('span');
          label.className = 'bbox-label';
          label.textContent = index;
          label.style.backgroundColor = color;
          div.appendChild(label);
          
          doc.body.appendChild(div);
        });
      }
      
      setIframeLoaded(true);
    } catch (err) {
      console.error('Error rendering DOM:', err);
    }
  }, [domData, bboxes]);

  if (!domData && !screenshot) {
    return (
      <Box sx={{ py: 4, textAlign: 'center' }}>
        <Typography variant="body1">No content available</Typography>
      </Box>
    );
  }

  return (
    <Paper 
      elevation={3} 
      sx={{ 
        height: '100%', 
        display: 'flex', 
        flexDirection: 'column',
        overflow: 'hidden'
      }}
    >
      <Tabs 
        value={viewMode} 
        onChange={(_, newValue) => setViewMode(newValue)} 
        sx={{ borderBottom: 1, borderColor: 'divider' }}
      >
        <Tab value="rendered" icon={<ImageRounded />} label="Live DOM" />
        <Tab value="screenshot" icon={<CodeRounded />} label="Screenshot" />
      </Tabs>
      
      <Box sx={{ flex: 1, overflow: 'auto', position: 'relative' }}>
        {viewMode === 'rendered' && (
          <Box
            sx={{
              display: iframeLoaded && domData ? 'block' : 'none',
              height: '100%',
            }}
          >
            <iframe
              ref={iframeRef}
              title="Page DOM"
              sandbox="allow-same-origin"
              style={{
                width: '100%',
                height: '100%',
                border: 'none',
              }}
              onLoad={() => setIframeLoaded(true)}
            />
          </Box>
        )}
        
        {(viewMode === 'screenshot' || !domData || !iframeLoaded) && screenshot && (
          <Box sx={{ p: 1, height: '100%', overflow: 'auto' }}>
            <img
              src={`data:image/png;base64,${screenshot}`}
              alt="Page screenshot"
              style={{ maxWidth: '100%' }}
            />
          </Box>
        )}
        
        {(!domData && !screenshot) && (
          <Box sx={{ p: 4, textAlign: 'center' }}>
            <Typography variant="body1">
              No content available
            </Typography>
          </Box>
        )}
      </Box>
    </Paper>
  );
}