'use client';

import React, { useState, useEffect } from 'react';
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
  useMediaQuery,
  Tabs,
  Tab,
  Divider,
  ThemeProvider
} from '@mui/material';
import { 
  Menu as MenuIcon, 
  Send as SendIcon, 
  Settings as SettingsIcon, 
  History as HistoryIcon,
  Computer as ComputerIcon,
  Chat as ChatIcon
} from '@mui/icons-material';
import { useViewport } from '../../contexts/ViewportContext';
import { useWebSocketContext } from '../../contexts/WebSocketContext';
import { MESSAGE_TYPES } from '../../services/websocket';
import ScreenshotViewer from '@/app/components/ScreenShowViewer';
import InterventionModal from '@/app/components/HumanInterventionModal';
import dynamic from 'next/dynamic';
import TestingPanel from '@/app/components/TestingPanel';

// Image Message Component
const ImageMessage = ({ src, alt = "Screenshot", sender, isUrl = false }) => {
  const theme = useTheme();
  const [enlarged, setEnlarged] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  
  // Image source can be either a URL or base64 data
  const imageSrc = isUrl ? src : `data:image/png;base64,${src}`;
  
  return (
    <>
      <Paper
        elevation={1}
        sx={{
          padding: 1,
          maxWidth: '80%',
          backgroundColor: sender === 'user' ? theme.palette.primary.main : theme.palette.grey[100],
          color: sender === 'user' ? '#fff' : 'inherit',
          alignSelf: sender === 'user' ? 'flex-end' : 'flex-start',
          overflow: 'hidden'
        }}
      >
        <Box sx={{ cursor: 'pointer' }} onClick={() => setEnlarged(true)}>
          {loading && <Typography sx={{ p: 2, textAlign: 'center' }}>Loading image...</Typography>}
          {error && <Typography sx={{ p: 2, textAlign: 'center', color: 'error.main' }}>Failed to load image</Typography>}
          <img 
            src={imageSrc}
            alt={alt}
            style={{ 
              width: '100%', 
              height: 'auto', 
              maxWidth: '100%', 
              display: loading ? 'none' : 'block', 
              borderRadius: '4px' 
            }} 
            onLoad={() => setLoading(false)}
            onError={() => {
              setLoading(false);
              setError(true);
            }}
          />
        </Box>
        <Typography variant="caption" sx={{ display: 'block', mt: 1, textAlign: 'center' }}>
          {!error && "Click to enlarge"}
          {error && "Image loading failed"}
        </Typography>
      </Paper>

      {enlarged && !error && (
        <Box
          onClick={() => setEnlarged(false)}
          sx={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0,0,0,0.8)',
            zIndex: 9999,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer'
          }}
        >
          <img 
            src={imageSrc}
            alt={alt}
            style={{ maxWidth: '90%', maxHeight: '90%', objectFit: 'contain' }}
            onClick={(e) => e.stopPropagation()}
          />
        </Box>
      )}
    </>
  );
};

// Message list component to show conversations
const MessageList = ({ messages, isProcessing }) => {
  const theme = useTheme();
  const messagesEndRef = React.useRef(null);
  
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <Box 
      sx={{ 
        display: 'flex',
        flexDirection: 'column',
        padding: 4,
        gap: 4,
        overflowY: 'auto',
        height: '100%'
      }}
    >
      {messages.map(message => (
        message.isImage ? (
          <ImageMessage 
            key={message.id}
            src={message.imageUrl || message.screenshot}
            isUrl={!!message.imageUrl}
            alt={`Step ${message.step} Screenshot`}
            sender={message.sender}
          />
        ) : (
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
        )
      ))}
      {isProcessing && (
        <Box sx={{ alignSelf: 'flex-start', padding: 2 }}>
          <Typography sx={{ color: 'text.secondary' }}>Processing...</Typography>
        </Box>
      )}
      <div ref={messagesEndRef} />
    </Box>
  );
};

// Chat header component
const ChatHeader = ({ toggleDrawer, isSmallScreen }) => {
  return (
    <AppBar position="static" color="default" sx={{ boxShadow: 1 }}>
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
  );
};

// Main chat input component
const ChatInput = ({ userInput, setUserInput, handleSendMessage, isProcessing, isConnected }) => {
  return (
    <Box sx={{ 
      display: 'flex', 
      alignItems: 'center',
      gap: 2,
      width: '100%'
    }}>
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
  );
};

// Sidebar component
const ConversationList = ({ drawerOpen }) => {
  const theme = useTheme();
  
  return (
    <Box sx={{ padding: 4 }}>
      <Typography 
        variant="h6" 
        component="div" 
        sx={{ marginBottom: 4 }}
      >
        LLM Agent
      </Typography>
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
  );
};

// Use client-side only rendering to avoid hydration issues
const ChatPage = () => {
  const [mounted, setMounted] = useState(false);
  const [isTesting, setIsTesting] = useState(false);
  const [testActions, setTestActions] = useState([]);
  const [isHumanIntervention, setIsHumanIntervention] = useState(true);

  useEffect(() => {
    setMounted(true);
  }, []);
  
  const { isMobile, isDesktop } = useViewport();
  const theme = useTheme();
  const isSmallScreen = useMediaQuery(theme.breakpoints.down('md'));
  const [drawerOpen, setDrawerOpen] = useState(!isSmallScreen);
  const [userInput, setUserInput] = useState('');
  const [messages, setMessages] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [activeTab, setActiveTab] = useState(0);
  const [interventionModalOpen, setInterventionModalOpen] = useState(false);
  const [currentScreenshot, setCurrentScreenshot] = useState(null);

  const { 
    isConnected, 
    messages: wsMessages, 
    sendQuery,
    sendHumanInterventionResponse,
    humanIntervention,
    screenshots, 
    error: wsError 
  } = useWebSocketContext();

  // Handle human intervention requests
  useEffect(() => {
    if (humanIntervention) {
      console.log("Human intervention requested:", humanIntervention);
      setInterventionModalOpen(true);
    }
  }, [humanIntervention]);
  
  // Handle screenshots
  useEffect(() => {
    if (currentSessionId && screenshots[currentSessionId]) {
      const sessionScreenshots = screenshots[currentSessionId];
      const steps = Object.keys(sessionScreenshots).map(Number).sort((a, b) => b - a);
      
      if (steps.length > 0) {
        const latestStep = steps[0];
        setCurrentScreenshot(sessionScreenshots[latestStep]);
      }
    }
  }, [screenshots, currentSessionId]);

  const isNarrowWindow = useMediaQuery('(max-width:1200px)');

  useEffect(() => {
    setDrawerOpen(!isNarrowWindow);
  }, [isNarrowWindow]);
  
  useEffect(() => {
    if (wsMessages.length > 0) {
      const latestMessage = wsMessages[wsMessages.length - 1];
      
      switch (latestMessage.type) {
        case MESSAGE_TYPES.SESSION_UPDATE:
          if (latestMessage.payload.session_id) {
            setCurrentSessionId(latestMessage.payload.session_id);
          }
          break;
          
        case MESSAGE_TYPES.SESSION_COMPLETED:
          setIsProcessing(false);
          setCurrentSessionId(null);
          
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
          
          case MESSAGE_TYPES.SCREENSHOT_UPDATE:
            // Now handle both URL and base64 formats
            if (latestMessage.payload.screenshot || latestMessage.payload.image_url) {
              // Store for browser view tab (use screenshot if available, otherwise null)
              setCurrentScreenshot(latestMessage.payload.screenshot || null);
              
              // Add to messages
              setMessages(prev => [
                ...prev,
                { 
                  id: `screenshot-${Date.now()}`,
                  sender: 'agent',
                  isImage: true,
                  screenshot: latestMessage.payload.screenshot,
                  imageUrl: latestMessage.payload.image_url,
                  step: latestMessage.payload.step || 'unknown',
                  sessionId: latestMessage.payload.session_id
                }
              ]);
            }
            break;
          
        case MESSAGE_TYPES.ERROR:
          console.error('WebSocket error:', latestMessage.payload);
          setIsProcessing(false);
          
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
  
  useEffect(() => {
    if (wsError) {
      console.error('WebSocket connection error:', wsError);
    }
  }, [wsError]);

  const toggleDrawer = () => {
    setDrawerOpen(prevState => !prevState);
  };

  const handleSendMessage = async () => {
    if (!userInput.trim() || isProcessing) return;
    
    setMessages(prev => [
      ...prev, 
      { id: `user-${Date.now()}`, text: userInput, sender: 'user' }
    ]);
    
    try {
      setIsProcessing(true);
      // Prepare test actions if testing mode is enabled
      const testConfig = isTesting ? {
        testing: true,
        test_actions: testActions.map(action => [action.type, action.args]),
        human_intervention: isHumanIntervention
      } : {};

      // Send the query with testing configuration if applicable
      const success = sendQuery(userInput, testConfig);

      if (!success) {
        throw new Error('Failed to send message: WebSocket not connected');
      }

      setUserInput('');
      // Switch back to chat tab after sending
      setActiveTab(0);
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

  const handleInterventionResponse = (response) => {
    if (humanIntervention && humanIntervention.session_id) {
      console.log("Sending human intervention response:", response);
      sendHumanInterventionResponse(humanIntervention.session_id, response || "");
      setInterventionModalOpen(false);
    }
  };

  const conversationlistWidth = 240;
  const appBarHeight = 64;
  const bottomBarMinHeight = 72;
  
  // Don't render until client-side
  if (!mounted) {
    return null;
  }
  
  return (
    <ThemeProvider theme={theme}>
      <Box
        component="div"
        sx={{
          height: '100vh',
          width: '100%',
          display: 'grid',
          mx: 0,
          gridTemplateColumns: {
            xs: '1fr',
            sm: drawerOpen ? `${conversationlistWidth}px 1fr` : '1fr',
            md: `${conversationlistWidth}px 1fr`,
          },
          gridTemplateRows: `${appBarHeight}px 1fr ${bottomBarMinHeight}px`,
          gridTemplateAreas: {
            xs: drawerOpen 
                ? `"sidebar topbar" "sidebar content" "sidebar bottombar"`
                : `"topbar" "content" "bottombar"`,
            sm: drawerOpen 
                ? `"sidebar topbar" "sidebar content" "sidebar bottombar"`
                : `"topbar" "content" "bottombar"`,
            md: `"sidebar topbar" "sidebar content" "sidebar bottombar"`,
          },
          position: 'relative',
        }}
      >
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
              {wsError ? 
                `Connection error: ${wsError}. Attempting to reconnect...` : 
                'Disconnected from server. Attempting to reconnect...'}
            </Typography>
          </Box>
        )}
        
        {/* Sidebar */}
        <Box 
          sx={{ 
            gridArea: 'sidebar',
            display: { 
              xs: drawerOpen ? 'block' : 'none',
              sm: drawerOpen ? 'block' : 'none', 
              md: 'block' 
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
          <ConversationList drawerOpen={drawerOpen} />
        </Box>
        
        {/* Top Bar */}
        <Box 
          sx={{ 
            gridArea: 'topbar',
            zIndex: 30
          }}
        >
          <ChatHeader 
            toggleDrawer={toggleDrawer} 
            isSmallScreen={isSmallScreen}
          />
        </Box>
        
        {/* Main Content */}
        <Box 
          sx={{ 
            gridArea: 'content',
            display: 'flex',
            flexDirection: 'column',
            height: '100%',
            overflow: 'hidden'
          }}
        >
          {/* View Tabs */}
          <Tabs 
            value={activeTab} 
            onChange={(_, newValue) => setActiveTab(newValue)}
            variant="fullWidth"
            sx={{ borderBottom: 1, borderColor: 'divider' }}
          >
            <Tab icon={<ChatIcon />} label="Chat" />
            <Tab icon={<ComputerIcon />} label="Browser View" />
          </Tabs>
          
          {/* Tab Panels */}
          <Box 
            sx={{ 
              flex: 1,
              overflow: 'auto',
              display: activeTab === 0 ? 'flex' : 'none',
              flexDirection: 'column'
            }}
          >
            <MessageList 
              messages={messages} 
              isProcessing={isProcessing}
            />
          </Box>
          
          {/* Browser View */}
          <Box 
            sx={{ 
              flex: 1,
              overflow: 'auto',
              padding: 3,
              display: activeTab === 1 ? 'block' : 'none',
            }}
          >
            <ScreenshotViewer 
              screenshot={currentScreenshot} 
              isLoading={isProcessing && !currentScreenshot}
              title="Agent Browser View"
            />
          </Box>
        </Box>
        
        {/* Bottom Input Area */}
        <Box 
          sx={{ 
            gridArea: 'bottombar',
            borderTop: 1,
            borderColor: 'divider',
            padding: 2,
            display: 'flex',
            flexDirection: 'column',
            backgroundColor: theme.palette.background.paper
          }}
        >
          <TestingPanel 
            isTesting={isTesting}
            onTestingChange={setIsTesting}
            testActions={testActions}
            onTestActionsChange={setTestActions}
            isHumanIntervention={isHumanIntervention}
            onHumanInterventionChange={setIsHumanIntervention}
          />
          
          <ChatInput 
            userInput={userInput}
            setUserInput={setUserInput}
            handleSendMessage={handleSendMessage}
            isProcessing={isProcessing}
            isConnected={isConnected}
          />
        </Box>
        
        {/* Human Intervention Modal */}
        <InterventionModal
          open={interventionModalOpen}
          onClose={() => setInterventionModalOpen(false)}
          interventionData={humanIntervention}
          onRespond={handleInterventionResponse}
        />
      </Box>
    </ThemeProvider>
  );
};

// Use dynamic import with no SSR for the whole page component
export default dynamic(() => Promise.resolve(ChatPage), {
  ssr: false
});