'use client';

import { Inter } from 'next/font/google';
import { ViewportProvider } from './contexts/ViewportContext';
import { WebSocketProvider } from './contexts/WebSocketContext';
import { createTheme, ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import React from 'react';


const inter = Inter({ subsets: ['latin'] });

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
    background: {
      default: '#f9f9f9',
      paper: '#ffffff',
    },
  },
  typography: {
    fontFamily: inter.style.fontFamily,
  },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          margin: 0,
          padding: 0,
          height: '100%',
          width: '100%',
          overflow: 'hidden',
        },
        html: {
          height: '100%',
          width: '100%',
        },
        '#__next': {
          height: '100%',
        },
      },
    },
  },
});

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="h-full">
      <body className={inter.className} id="__next">
        <ThemeProvider theme={theme}>
          <CssBaseline />
          <ViewportProvider>
            <WebSocketProvider>
              {children}
            </WebSocketProvider>
          </ViewportProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}