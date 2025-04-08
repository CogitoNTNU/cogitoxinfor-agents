import { ViewportProvider } from './contexts/ViewportContext';
import { WebSocketProvider } from './contexts/WebSocketContext';
import './globals.css';

export const metadata = {
  title: 'Chat Application',
  description: 'A real-time chat application built with Next.js',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <ViewportProvider>
          <WebSocketProvider>
            {children}
          </WebSocketProvider>
        </ViewportProvider>
      </body>
    </html>
  );
}