"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation"; // Updated import for Next.js 13+ App Router

export default function Home() {
  const router = useRouter(); // Initialize router
  const [mounted, setMounted] = useState(false);

  // IMPORTANT: Move ALL useEffect hooks before any conditional returns
  useEffect(() => {
    setMounted(true);
    
    // Add routing logic here
    // This will execute once when component mounts
    if (typeof window !== 'undefined') {
      // You can add conditions before routing if needed
      router.push('/app/chat');
    }
  }, [router]);

  // After ALL hooks are defined, THEN you can have conditional returns
  if (!mounted) {
    return null;
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-screen py-2">
      <h1 className="text-4xl font-bold mb-4">Welcome to LangGraph</h1>
      <p className="text-lg mb-8">Your AI-powered language learning companion.</p>
    </div>
  );
}