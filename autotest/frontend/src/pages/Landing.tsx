import React from 'react';
import LandingChatbox from '../components/LandingChatbox';
import { BlurFade } from "@/components/magicui/blur-fade";
import { AnimatedShinyText } from "@/components/magicui/animated-shiny-text";


const Landing: React.FC = () => {
  return (
    <section className="min-h-screen py-16 md:py-24 animated-gradient flex items-center justify-center">
      <div className="container px-4 md:px-6 mx-auto text-center">
        <div className="max-w-3xl mx-auto space-y-6 mb-16">
          <BlurFade delay={0.3} inView>
            <h1 className="text-4xl md:text-6xl font-bold tracking-tighter text-white">
              <span className="block">AI-Powered</span>
              <span className="block">Test Automation</span>
            </h1>
          </BlurFade>
          
          <BlurFade delay={0.5} inView>
            <div className="flex flex-col md:flex-row items-center justify-center md:gap-2 text-lg md:text-xl text-gray-100 whitespace-nowrap">
              <div className="flex items-center">
                <span className="bg-white/30 rounded-full h-10 w-10 flex items-center justify-center mr-2 text-white shadow-inner border border-white/20">1</span>
                <p>AI browses</p>
              </div>
              <div className="hidden md:block text-white">→</div>
              <div className="flex items-center">
                <span className="bg-white/30 rounded-full h-10 w-10 flex items-center justify-center mr-2 text-white shadow-inner border border-white/20">2</span>
                <p>Logs each step</p>
              </div>
              <div className="hidden md:block text-white">→</div>
              <div className="flex items-center">
                <span className="bg-white/30 rounded-full h-10 w-10 flex items-center justify-center mr-2 text-white shadow-inner border border-white/20">3</span>
                <p>Generates tests</p>
              </div>
            </div>
          </BlurFade>
        </div>
        
        <BlurFade delay={0.7} inView>
          <div className="max-w-3xl mx-auto">
            <LandingChatbox />
          </div>
        </BlurFade>
        
        <BlurFade delay={1.2} inView>
        <div
        className="group mx-auto w-[17rem] rounded-full border border-black/5 bg-neutral-100 text-base text-white transition-all ease-in hover:cursor-pointer hover:bg-neutral-200 dark:border-white/5 dark:bg-neutral-900 dark:hover:bg-neutral-800"
        >
        <AnimatedShinyText className="inline-flex items-center justify-center px-4 py-1 transition ease-out hover:text-neutral-600 hover:duration-300 hover:dark:text-neutral-400">
          <span>⚡ Powered by Cogito × Infor ⚡</span>
        </AnimatedShinyText>
        </div>
        </BlurFade>
      </div>
      
    </section>
  );
};

export default Landing;
