'use client';

import { useState, useEffect } from 'react';
import { 
  Box, 
  AppBar, 
  Toolbar, 
  TextField, 
  IconButton, 
  Typography, 
  List, 
  ListItemButton,
  ListItemText, 
  ListItemIcon,
  Paper,
  useTheme,
  useMediaQuery
} from '@mui/material';
import { 
  Menu as MenuIcon, 
  Send as SendIcon, 
  Settings as SettingsIcon, 
  History as HistoryIcon 
} from '@mui/icons-material';
import { useViewport } from '../../contexts/ViewportContext';
import { useWebSocketContext } from '../../contexts/WebSocketContext';
import { MESSAGE_TYPES } from '../../services/websocket';

export default function ChatPage() {
  const { isMobile, isDesktop } = useViewport();
  const theme = useTheme();
  const isSmallScreen = useMediaQuery(theme.breakpoints.down('md'));
  const [drawerOpen, setDrawerOpen] = useState(!isSmallScreen);
  const [userInput, setUserInput] = useState('');
  const [messages, setMessages] = useState<Array<{id: string, text: string, sender: 'user' | 'agent'}>>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);

  // Use WebSocket context
  const { 
    isConnected, 
    messages: wsMessages, 
    sendQuery, 
    error: wsError 
  } = useWebSocketContext();
    

  useEffect(() => {
    console.log("Drawer state changed to:", drawerOpen);
  }, [drawerOpen]);


// More specific control - create a custom breakpoint
const isNarrowWindow = useMediaQuery('(max-width:1200px)'); // Adjust pixel value as needed

useEffect(() => {
  setDrawerOpen(!isNarrowWindow);
}, [isNarrowWindow]);
  
  // Process WebSocket messages
  useEffect(() => {
    if (wsMessages.length > 0) {
      // Get the latest message
      const latestMessage = wsMessages[wsMessages.length - 1];
      
      switch (latestMessage.type) {
        case MESSAGE_TYPES.SESSION_UPDATE:
          // Update session status (e.g., processing)
          if (latestMessage.payload.session_id) {
            setCurrentSessionId(latestMessage.payload.session_id);
          }
          break;
          
        case MESSAGE_TYPES.SESSION_COMPLETED:
          // Session completed, update UI
          setIsProcessing(false);
          setCurrentSessionId(null);
          
          // Add agent response to messages
          if (latestMessage.payload.result) {
            setMessages(prev => [
              ...prev,
              { 
                id: `agent-${Date.now()}`,
                text: typeof latestMessage.payload.result === 'object' 
                  ? JSON.stringify(latestMessage.payload.result)
                  : String(latestMessage.payload.result),
                sender: 'agent'
              }
            ]);
          }
          break;
          
        case MESSAGE_TYPES.ERROR:
          // Handle error
          console.error('WebSocket error:', latestMessage.payload);
          setIsProcessing(false);
          
          // Add error message
          setMessages(prev => [
            ...prev,
            { 
              id: `error-${Date.now()}`,
              text: latestMessage.payload.message || 'Failed to process your request. Please try again.',
              sender: 'agent'
            }
          ]);
          break;
      }
    }
  }, [wsMessages]);
  
  // Show connection error
  useEffect(() => {
    if (wsError) {
      console.error('WebSocket connection error:', wsError);
    }
  }, [wsError]);
  

// Handle drawer toggle
const toggleDrawer = () => {
  console.log("Toggle drawer clicked. Current state:", drawerOpen);
  setDrawerOpen(prevState => {
    console.log("Setting drawer to:", !prevState);
    return !prevState;
  });
};

  // Handle sending a message
  const handleSendMessage = async () => {
    if (!userInput.trim() || isProcessing) return;
    
    setMessages(prev => [
      ...prev, 
      { id: `user-${Date.now()}`, text: userInput, sender: 'user' }
    ]);
    
    try {
      setIsProcessing(true);
      const success = sendQuery(userInput);
      
      if (!success) {
        throw new Error('Failed to send message: WebSocket not connected');
      }
      
      setUserInput('');
    } catch (error) {
      console.error('Error sending message:', error);
      setIsProcessing(false);
      
      setMessages(prev => [
        ...prev,
        { 
          id: `error-${Date.now()}`,
          text: 'Failed to send your message. Please check your connection and try again.',
          sender: 'agent'
        }
      ]);
    }
  };

  // Layout constants
  const conversationlistWidth = 240;
  const appBarHeight = 64;
  const bottomBarMinHeight = 72;
  
  return (
    // Fix 3: Simplify grid template
    <Box
      component="div"
      sx={{
        height: '100%',
        width: '100%',
        display: 'grid',
        mx: 0,
        gridTemplateColumns: {
          xs: '1fr',
          sm: drawerOpen ? `${conversationlistWidth}px 1fr` : '1fr',
          md: `${conversationlistWidth}px 1fr`, // Always reserve space for sidebar on desktop
        },
        gridTemplateRows: `${appBarHeight}px 1fr ${bottomBarMinHeight}px`,
        gridTemplateAreas: {
          xs: drawerOpen 
              ? `"sidebar topbar" "sidebar content" "sidebar bottombar"`
              : `"topbar" "content" "bottombar"`,
          sm: drawerOpen 
              ? `"sidebar topbar" "sidebar content" "sidebar bottombar"`
              : `"topbar" "content" "bottombar"`,
          md: `"sidebar topbar" "sidebar content" "sidebar bottombar"`, // Fixed layout for desktop
        },
        position: 'relative',
      }}
    >
      {/* Connection status indicator */}
      {!isConnected && (
        <Box 
          sx={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            backgroundColor: 'error.main',
            color: 'white',
            padding: 1,
            textAlign: 'center',
            zIndex: 50
          }}
        >
          <Typography variant="body2">
            Disconnected from server. Attempting to reconnect...
          </Typography>
        </Box>
      )}
      
      {/* Sidebar */}
      <Box 
        sx={{ 
          gridArea: 'sidebar',
          display: { 
            xs: drawerOpen ? 'block' : 'none', // Show on mobile if drawer is open
            sm: drawerOpen ? 'block' : 'none', 
            md: 'block' // Always show on desktop
          },
          width: conversationlistWidth,
          borderRight: 1,
          borderColor: 'divider',
          backgroundColor: theme.palette.background.paper,
          overflowY: 'auto',
          position: 'relative',
          zIndex: 10
        }}
      >
        <Box sx={{ padding: 4 }}>
          <Typography 
            variant="h6" 
            component="div" 
            sx={{ marginBottom: 4 }}
          >
            LLM Agent
          </Typography>
        </Box>
        <List>
          <ListItemButton 
            sx={{ '&:hover': { backgroundColor: 'grey.100' } }}
          >
            <ListItemIcon><HistoryIcon /></ListItemIcon>
            <ListItemText primary="History" />
          </ListItemButton>
          <ListItemButton 
            sx={{ '&:hover': { backgroundColor: 'grey.100' } }}
          >
            <ListItemIcon><SettingsIcon /></ListItemIcon>
            <ListItemText primary="Settings" />
          </ListItemButton>
        </List>
      </Box>
      
      {/* Top Bar */}
      <AppBar 
        position="static" 
        color="default"
        sx={{ 
          gridArea: 'topbar',
          boxShadow: 1
        }}
      >
        <Toolbar>
          {isSmallScreen && (
            <IconButton 
              color="inherit" 
              edge="start" 
              onClick={toggleDrawer} 
              sx={{ marginRight: 2 }}
            >
              <MenuIcon />
            </IconButton>
          )}
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            Chat
          </Typography>
        </Toolbar>
      </AppBar>
      
      {/* Main Content */}
      <Box 
        sx={{ 
          gridArea: 'content',
          display: 'flex',
          flexDirection: 'column',
          padding: 4,
          overflowY: 'auto',
          gap: 4
        }}
      >
        {messages.map(message => (
          <Paper 
            key={message.id}
            elevation={1}
            sx={{
              padding: 3,
              maxWidth: '80%',
              backgroundColor: message.sender === 'user' ? theme.palette.primary.main : theme.palette.grey[100],
              color: message.sender === 'user' ? '#fff' : 'inherit',
              alignSelf: message.sender === 'user' ? 'flex-end' : 'flex-start'
            }}
          >
            <Typography>{message.text}</Typography>
          </Paper>
        ))}
        {isProcessing && (
          <Box sx={{ alignSelf: 'flex-start', padding: 2 }}>
            <Typography sx={{ color: 'text.secondary' }}>Processing...</Typography>
          </Box>
        )}
      </Box>
      
      {/* Bottom Input Area */}
      <Box 
        sx={{ 
          gridArea: 'bottombar',
          borderTop: 1,
          borderColor: 'divider',
          padding: 2,
          display: 'flex',
          alignItems: 'center',
          gap: 2
        }}
      >
        <TextField
          fullWidth
          variant="outlined"
          placeholder="Type your message..."
          value={userInput}
          onChange={(e) => setUserInput(e.target.value)}
          onKeyPress={(e) => {
            if (e.key === 'Enter') {
              handleSendMessage();
            }
          }}
          disabled={isProcessing || !isConnected}
          sx={{ 
            backgroundColor: 'white',
            borderRadius: 1
          }}
          size="small"
        />
        <IconButton 
          color="primary" 
          onClick={handleSendMessage}
          disabled={isProcessing || !userInput.trim() || !isConnected}
        >
          <SendIcon />
        </IconButton>
      </Box>
    </Box>
  );
}