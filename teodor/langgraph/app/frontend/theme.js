// theme.js
import { createTheme } from '@mui/material/styles';

const theme = createTheme({
  palette: {
    primary: {
      main: '#1E90FF', // Dodger Blue for secondary elements
    },
    secondary: {
      main: '#1E90FF', // Light blue for main headers and other details
      black: '#000000', // Black for secondary elements
    },
    background: {
      white: '#ffffff', // White background
    },
    text: {
      primary: '#000000', // Black text color
      secondary: '#666666', // Gray for secondary text
    },
    message: {
      userMessage: '#f5f5f5', // Light blue for sent messages
      aiMessage: '#96d3eb', // Light gray for received messages
      code: '#96d3eb', // Light blue for code messages
    },
    appBar: {
      default: '#f5f5f5', // Custom default color for AppBar
    },
    hjalp: {
      main: '#54504C',  // Dark gray for Hjælp main headers and elements
      secondary: '#8dff96', // Light green for focus items
      background: '#FCFAF4', // Light yellow for Hjælp background
      black: '#000000', // Black for Hjælp text
    },
  },
  shape: {
    borderRadius: "8px",
  },
  typography: {
      hjalp: {
          fontFamily: 'Gopher-Bold, sans-serif',
          fontSize: '23px',
          lineHeight: '150%',
          letterSpacing: '-0.15px',
          fontWeight: 700,
          regular: {
            fontFamily: 'Gopher-Regular, sans-serif',
            fontSize: '15px',
            fontWeight: 400,
          },
          bold: {
            fontFamily: 'Gopher-Bold, sans-serif',
            fontSize: '23px',
            fontWeight: 700,
        },
      },
  },
});

export default theme;