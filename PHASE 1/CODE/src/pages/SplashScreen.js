import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

export default function SplashScreen() {
  const navigate = useNavigate();

  const handleGetStarted = () => {
    const hasSeenOnboarding = localStorage.getItem('wrapture_onboarding_completed');
    if (hasSeenOnboarding === 'true') {
      navigate('/');
    } else {
      navigate('/onboarding');
    }
  };

  // Optional auto-redirect after short delay if user doesn't tap Get Started
  useEffect(() => {
    const timer = setTimeout(() => {
      // Don't auto-redirect immediately, allow user to appreciate splash or tap button
    }, 3000);
    return () => clearTimeout(timer);
  }, [navigate]);

  return (
    <div className="w-full h-full min-h-screen text-on-surface font-body-md relative overflow-hidden select-none bg-surface flex flex-col justify-between">
      {/* Immersive Full-Bleed Photographic Background Layer */}
      <div className="absolute inset-0 w-full h-full z-0 overflow-hidden">
        <img
          alt="Wrapture bespoke sustainable kraft packaging hero"
          className="w-full h-full object-cover object-center pointer-events-none"
          src="/assets/hero-kraft-packaging.png"
        />
        {/* Subtle, delicate sunlight & contrast scrims */}
        <div className="absolute inset-0 bg-gradient-to-b from-[#FAF7F1]/60 via-transparent via-40% to-[#183325]/45 pointer-events-none"></div>
        <div className="absolute inset-x-0 top-0 h-48 bg-gradient-to-b from-[#FAF7F1]/80 to-transparent pointer-events-none"></div>
      </div>

      {/* Content Layer: Seamless Editorial Mobile Splash Layout */}
      <main className="relative z-10 flex flex-col justify-between w-full h-full min-h-screen pt-safe pb-safe px-6 max-w-md mx-auto">
        {/* Top Area: Brand Lockup & Asymmetrical Statement */}
        <header className="flex flex-col w-full pt-4">
          <div className="flex items-center space-x-3.5">
            <svg 
              className="w-8 h-8 text-primary shrink-0" 
              viewBox="0 0 24 24" 
              fill="none" 
              stroke="currentColor" 
              strokeWidth="1.75"
            >
              <path d="M12 2C7 6.5 4 12 4 17a8 8 0 0 0 16 0c0-5-3-10.5-8-15z" strokeLinecap="round" strokeLinejoin="round"></path>
              <path d="M12 2v20M12 7l5 3M12 12l5 3M12 17l4 2.5M12 7l-5 3M12 12l-5 3M12 17l-4 2.5" strokeLinecap="round" strokeLinejoin="round"></path>
            </svg>
            <div className="flex flex-col justify-center">
              <span className="font-serif font-semibold tracking-[0.22em] text-primary text-[19px] uppercase leading-none">
                WRAPTURE
              </span>
              <span className="font-label-caps tracking-[0.28em] font-semibold text-primary/70 text-[10px] uppercase mt-1">
                INTELLIGENT PACKAGING
              </span>
            </div>
          </div>

          <div className="mt-10 max-w-[320px]">
            <h1 className="font-serif">
              <span className="block text-4xl sm:text-5xl font-normal text-primary tracking-[-0.02em] leading-[1.05]">
                Smart Packaging.
              </span>
              <span className="block text-4xl sm:text-5xl italic font-normal text-primary/90 tracking-[-0.02em] leading-[1.05] mt-1">
                Less Waste.
              </span>
            </h1>
          </div>
        </header>

        {/* Clear center breathing viewport space */}
        <div className="flex-1 pointer-events-none min-h-[160px]"></div>

        {/* Bottom Area: Understated supporting metadata & CTA */}
        <footer className="flex flex-col w-full space-y-4 pb-4">
          <div className="flex items-center justify-between w-full pb-2.5 border-b border-primary/20">
            <span className="font-label-caps tracking-[0.22em] text-[10px] font-semibold uppercase text-primary/90">
              AI PACKAGING INTELLIGENCE
            </span>
            <span className="font-label-caps tracking-[0.18em] text-[10px] font-medium uppercase text-primary/75">
              PRODUCT → MATERIAL → PACKAGE
            </span>
          </div>

          <div className="w-full pt-1">
            <button
              onClick={handleGetStarted}
              type="button"
              className="w-full py-4 px-6 rounded-full bg-primary text-surface flex items-center justify-between shadow-xl shadow-primary/20 hover:bg-primary-container active:scale-[0.99] transition-all duration-300 group cursor-pointer"
            >
              <span className="font-label-caps tracking-[0.2em] text-[12px] font-semibold uppercase text-surface">
                Get Started
              </span>
              <span className="material-symbols-outlined text-[19px] text-surface transition-transform duration-300 group-hover:translate-x-1">
                arrow_forward
              </span>
            </button>
          </div>

          {/* Subtle minimal progress shimmer indicator line */}
          <div className="w-full pt-0.5">
            <div className="w-full h-[1.5px] bg-primary/20 rounded-full overflow-hidden relative">
              <div className="w-24 h-full bg-primary/80 rounded-full animate-shimmer"></div>
            </div>
          </div>
        </footer>
      </main>
    </div>
  );
}
