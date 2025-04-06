'use client';

import { Box, Typography, Button } from '@mui/material';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

export default function Home() {
  const [isMounted, setIsMounted] = useState(false);
  const router = useRouter();
  
  useEffect(() => {
    setIsMounted(true);
  }
  , []);
  // Check if the component is mounted before rendering
  if (!isMounted) {
    return null;
  }
  else {
    router.push('/app/chat')
  }

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        padding: 4,
        textAlign: 'center'
      }}
    >
      <Typography variant="h2" component="h1" gutterBottom>
        Welcome to LLM Agent
      </Typography>
      
      <Typography variant="body1" paragraph>
        This application lets you interact with an AI assistant through a chat interface.
      </Typography>
      
    </Box>
  );
}