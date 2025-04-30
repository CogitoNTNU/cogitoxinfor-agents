import React from 'react';
import LandingChatbox from '../components/LandingChatbox';
import { BlurFade } from "@/components/magicui/blur-fade";
import { AnimatedShinyText } from "@/components/magicui/animated-shiny-text";

const fillChatInput = (text: string) => {
  const container = document.getElementById('landing-chatbox');
  if (!container) return;
  container.dispatchEvent(new CustomEvent('fillChatInput', { detail: { text } }));
};

const handleBuyPS5 = () => {
  fillChatInput(
    'Search on finn.no for a ps5 controller and message the owner that i want it for 80% of the price.'
  );
};

const handleTestWebsite = () => {
  fillChatInput(
    'open http://localhost:8080/ and enter the prompt "Open wikipedia and search for Trump". Wait 10 seconds then press the stopbutton. Click on the test generation tab. Click generate test. Click run test.'
  );
};

const handleAnswerMail = () => {
  fillChatInput('Open outlook and answer my most recent mail.');
};

const handleFindFlights = () => {
  fillChatInput(
    'On booking.com search for flights from Oslo to Singapore in june and select the best one.'
  );
};


const Landing: React.FC = () => {
  return (
    <section className="min-h-screen py-16 md:py-24 animated-gradient flex items-center justify-center">
      <div className="container px-4 md:px-6 mx-auto text-center">
        <div className="max-w-3xl mx-auto space-y-6 mb-16">
          <BlurFade delay={0.3} inView>
            <h1 className="text-4xl md:text-6xl font-bold tracking-tighter text-white">
              <span className="block">Test Any Website</span>
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
          <div id="landing-chatbox" className="max-w-3xl mx-auto">
            <LandingChatbox />
          </div>

      <div className="flex flex-wrap justify-center pt-0!">
      <button
        onClick={handleBuyPS5}
        className="rounded-full text-white px-3 m-2 py-2 bg-yellow-500/30"
      >
        Buy me a PS5 on finn.no
      </button>

      <button
        onClick={handleTestWebsite}
        className="rounded-full text-white px-3 m-2 py-2 bg-blue-500/50"
      >
        Test this website
      </button>

      <button
        onClick={handleAnswerMail}
        className="rounded-full text-white px-3 m-2 py-2 bg-green-500/50"
      >
        Answer my latest mail
      </button>

      <button
        onClick={handleFindFlights}
        className="rounded-full text-white px-3 m-2 py-2 bg-purple-500/50"
      >
        Find flights from Oslo to Singapore
      </button>
    </div>
        </BlurFade>


        
        <BlurFade delay={1.2} inView>
        <AnimatedShinyText className="inline-flex items-center justify-center px-4 py-1 text-white transition ease-out hover:text-neutral-600 hover:duration-300 hover:dark:text-neutral-400">
          <span>⚡ Powered by Cogito × Infor ⚡</span>
        </AnimatedShinyText>
        </BlurFade>
      </div>
      
    </section>
  );
};

export default Landing;
