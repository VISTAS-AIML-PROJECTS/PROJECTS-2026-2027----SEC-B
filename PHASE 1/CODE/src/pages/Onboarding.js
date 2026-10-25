import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const ONBOARDING_STEPS = [
  {
    step: 1,
    badge: 'AI PRODUCT DETECTION',
    title: 'Packaging should fit the product.',
    subtitle: 'Not the other way around.',
    description: 'Wrapture uses computer vision to detect your product category and retrieve verified physical dimensions from our comprehensive ABO catalog.',
    flow: ['Product', 'Category', 'Dimensions'],
    image: '/assets/hero-kraft-packaging.png',
  },
  {
    step: 2,
    badge: 'BIOMATERIAL CLASSIFICATION',
    title: 'Verify material integrity.',
    subtitle: 'From cardboard to compost.',
    description: 'Our trained MobileNetV2 classifier evaluates packaging materials across 7 classes to ensure optimal circular economy lifecycle compatibility.',
    flow: ['Substrate', 'Classification', 'Purity'],
    image: '/assets/cardboard-macro.png',
  },
  {
    step: 3,
    badge: 'PACKRIFT CATALOG INTEGRATION',
    title: 'Real verified packaging.',
    subtitle: 'Over 2,200 real catalog specs.',
    description: 'Access 2,209 real industrial packaging records: boxes, mailers, and protective sleeves with verified unit pricing, pack quantities, and physical constraints.',
    flow: ['Catalog', 'Fit Filter', 'Pricing'],
    image: '/assets/hero-kraft-packaging.png',
  },
  {
    step: 4,
    badge: 'DIMENSIONAL OPTIMIZATION',
    title: 'Eliminate void space.',
    subtitle: 'Reduce transport footprint.',
    description: 'Deterministic 3D algorithm tests physical rotation, 10% clearance boundaries, and protective cushioning to recommend the lowest-volume package.',
    flow: ['Optimization', '3D Fit', 'CO₂ Impact'],
    image: '/assets/hero-kraft-packaging.png',
  },
];

export default function Onboarding() {
  const navigate = useNavigate();
  const [currentStepIndex, setCurrentStepIndex] = useState(0);

  const step = ONBOARDING_STEPS[currentStepIndex];

  const handleFinish = () => {
    localStorage.setItem('wrapture_onboarding_completed', 'true');
    navigate('/');
  };

  const handleNext = () => {
    if (currentStepIndex < ONBOARDING_STEPS.length - 1) {
      setCurrentStepIndex(currentStepIndex + 1);
    } else {
      handleFinish();
    }
  };

  const handleSkip = () => {
    handleFinish();
  };

  return (
    <div className="bg-surface text-on-surface font-body-md min-h-screen flex flex-col justify-between pt-safe pb-safe px-5 max-w-md mx-auto">
      {/* Top Header */}
      <header className="w-full flex items-center justify-between py-3">
        <div className="flex items-center space-x-2">
          <svg className="w-6 h-6 text-primary flex-shrink-0" fill="none" viewBox="0 0 28 28" xmlns="http://www.w3.org/2000/svg">
            <path d="M14 2L24 7.5V20.5L14 26L4 20.5V7.5L14 2Z" stroke="currentColor" strokeLinejoin="round" strokeWidth="1.5"></path>
            <path d="M14 2V26" stroke="currentColor" strokeLinecap="round" strokeWidth="1.2"></path>
            <path d="M14 8L20 12" stroke="currentColor" strokeLinecap="round" strokeWidth="1.2"></path>
            <path d="M14 14L22 18" stroke="currentColor" strokeLinecap="round" strokeWidth="1.2"></path>
            <path d="M14 8L8 12" stroke="currentColor" strokeLinecap="round" strokeWidth="1.2"></path>
            <path d="M14 14L6 18" stroke="currentColor" strokeLinecap="round" strokeWidth="1.2"></path>
          </svg>
          <div className="flex flex-col">
            <span className="font-serif text-primary tracking-widest leading-none font-semibold text-[13px]">WRAPTURE</span>
            <span className="font-label-caps text-[8px] text-primary/70 tracking-[0.2em] leading-tight mt-0.5">INTELLIGENT PACKAGING</span>
          </div>
        </div>

        <button
          onClick={handleSkip}
          className="py-1 px-3 text-secondary hover:text-primary transition-colors font-label-caps text-xs tracking-wider uppercase font-semibold cursor-pointer"
          type="button"
        >
          Skip
        </button>
      </header>

      {/* Editorial Narrative */}
      <section className="mt-4 mb-2 flex flex-col">
        <span className="font-label-caps text-[10px] tracking-[0.2em] text-secondary font-bold uppercase mb-2">
          {step.badge}
        </span>
        <h1 className="font-serif text-3xl text-primary tracking-tight leading-[1.15]">
          {step.title}<br />
          <span className="italic font-normal">{step.subtitle}</span>
        </h1>
        <p className="font-body-md text-sm text-on-surface-variant mt-3 leading-relaxed">
          {step.description}
        </p>
      </section>

      {/* Process telemetry pill */}
      <div className="flex items-center justify-between bg-surface-container/70 rounded-xl px-4 py-2.5 my-3 border border-outline-variant/30">
        <div className="flex items-center space-x-1.5">
          <span className="material-symbols-outlined text-[16px] text-primary">inventory_2</span>
          <span className="font-label-caps text-[10px] uppercase tracking-wider font-semibold text-primary">{step.flow[0]}</span>
        </div>
        <span className="material-symbols-outlined text-[14px] text-on-surface-variant/50">arrow_forward</span>
        <div className="flex items-center space-x-1.5">
          <span className="material-symbols-outlined text-[16px] text-primary">eco</span>
          <span className="font-label-caps text-[10px] uppercase tracking-wider font-semibold text-primary">{step.flow[1]}</span>
        </div>
        <span className="material-symbols-outlined text-[14px] text-on-surface-variant/50">arrow_forward</span>
        <div className="flex items-center space-x-1.5">
          <span className="material-symbols-outlined text-[16px] text-primary">deployed_code</span>
          <span className="font-label-caps text-[10px] uppercase tracking-wider font-semibold text-primary">{step.flow[2]}</span>
        </div>
      </div>

      {/* Center Photography Plate */}
      <section className="w-full my-2 flex-1 flex flex-col justify-center">
        <div className="relative w-full rounded-2xl overflow-hidden bg-surface-container shadow-md aspect-[4/3] flex items-center justify-center border border-outline-variant/30">
          <img
            alt="Sustainable packaging studio photograph"
            className="w-full h-full object-cover transition-all duration-500 ease-out"
            src={step.image}
          />
          <div className="absolute inset-0 pointer-events-none bg-gradient-to-t from-primary/20 via-transparent to-transparent"></div>
        </div>
      </section>

      {/* Actions & Onboarding Cadence */}
      <footer className="mb-2 flex flex-col items-center w-full mt-4">
        <button
          onClick={handleNext}
          className="w-full bg-primary-container text-on-primary py-4 px-6 rounded-xl font-label-mono-data text-sm font-medium tracking-wide flex items-center justify-center space-x-2 shadow-md hover:bg-primary transition-all active:scale-[0.99] cursor-pointer"
          type="button"
        >
          <span>{currentStepIndex === ONBOARDING_STEPS.length - 1 ? 'Get Started with Wrapture' : 'Continue'}</span>
          <span className="material-symbols-outlined text-[18px]">arrow_forward</span>
        </button>

        {/* 4-dot indicator */}
        <div aria-label={`Step ${currentStepIndex + 1} of 4`} className="flex items-center justify-center space-x-2 mt-4">
          {ONBOARDING_STEPS.map((_, idx) => (
            <div
              key={idx}
              className={`transition-all duration-300 rounded-full ${
                idx === currentStepIndex
                  ? 'w-6 h-1.5 bg-primary-container'
                  : 'w-1.5 h-1.5 bg-surface-container-highest'
              }`}
            />
          ))}
        </div>
      </footer>
    </div>
  );
}
