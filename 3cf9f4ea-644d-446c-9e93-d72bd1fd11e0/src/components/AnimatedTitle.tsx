import React from 'react';
export function AnimatedTitle() {
  return <div className="relative">
      <h1 className="text-6xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-sjsu-blue via-sjsu-gold to-sjsu-blue animate-text-shimmer bg-[length:200%_auto]">
        AI Mock Interviewer
      </h1>
      <div className="mt-2 text-xl font-medium text-sjsu-darkBlue/70 animate-float">
        By SJSU, for SJSU
      </div>
    </div>;
}