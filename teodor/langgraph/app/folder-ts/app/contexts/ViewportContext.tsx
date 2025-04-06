import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

type ViewportSize = 'mobile' | 'tablet' | 'desktop';

interface ViewportContextType {
  viewportSize: ViewportSize;
  isMobile: boolean;
  isTablet: boolean;
  isDesktop: boolean;
}

const ViewportContext = createContext<ViewportContextType>({
  viewportSize: 'desktop',
  isMobile: false,
  isTablet: false,
  isDesktop: true,
});

export const useViewport = () => useContext(ViewportContext);

interface ViewportProviderProps {
  children: ReactNode;
}

export const ViewportProvider: React.FC<ViewportProviderProps> = ({ children }) => {
  const [viewportSize, setViewportSize] = useState<ViewportSize>('desktop');
  
  useEffect(() => {
    const handleResize = () => {
      const width = window.innerWidth;
      if (width < 600) {
        setViewportSize('mobile');
      } else if (width < 960) {
        setViewportSize('tablet');
      } else {
        setViewportSize('desktop');
      }
    };
    
    // Initial check
    handleResize();
    
    // Add event listener
    window.addEventListener('resize', handleResize);
    
    // Cleanup
    return () => window.removeEventListener('resize', handleResize);
  }, []);
  
  const value = {
    viewportSize,
    isMobile: viewportSize === 'mobile',
    isTablet: viewportSize === 'tablet',
    isDesktop: viewportSize === 'desktop',
  };
  
  return (
    <ViewportContext.Provider value={value}>
      {children}
    </ViewportContext.Provider>
  );
};