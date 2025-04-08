'use client';

import { createContext, useContext, useState, useEffect } from 'react';

const ViewportContext = createContext({
  isMobile: false,
  isDesktop: true
});

export function ViewportProvider({ children }) {
  const [isMobile, setIsMobile] = useState(false);
  const [isDesktop, setIsDesktop] = useState(true);

  useEffect(() => {
    const checkViewport = () => {
      setIsMobile(window.innerWidth < 768);
      setIsDesktop(window.innerWidth >= 1024);
    };
    
    // Initial check
    checkViewport();
    
    // Add event listener
    window.addEventListener('resize', checkViewport);
    
    // Cleanup
    return () => window.removeEventListener('resize', checkViewport);
  }, []);

  return (
    <ViewportContext.Provider value={{ isMobile, isDesktop }}>
      {children}
    </ViewportContext.Provider>
  );
}

export function useViewport() {
  return useContext(ViewportContext);
}