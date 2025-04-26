'use client';

import { createTheme } from '@mui/material/styles';

const theme = createTheme({
  typography: {
    fontFamily: 'var(--font-geist-sans)',
    mono: 'var(--font-geist-mono)',
  },
  palette: {
    mode: 'light',
    primary: {
      main: '#2563eb',
    },
    secondary: {
      main: '#4f46e5',
    },
  },
});

export default theme;