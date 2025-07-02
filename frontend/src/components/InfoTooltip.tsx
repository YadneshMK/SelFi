import { HelpCircle } from 'lucide-react';
import { useState } from 'react';

interface InfoTooltipProps {
  text: string;
}

export function InfoTooltip({ text }: InfoTooltipProps) {
  const [isVisible, setIsVisible] = useState(false);

  return (
    <div className="relative inline-block ml-1">
      <button
        type="button"
        onMouseEnter={() => setIsVisible(true)}
        onMouseLeave={() => setIsVisible(false)}
        onFocus={() => setIsVisible(true)}
        onBlur={() => setIsVisible(false)}
        className="inline-flex items-center justify-center"
        aria-label="More information"
      >
        <HelpCircle className="h-3 w-3 text-gray-400 hover:text-gray-600 cursor-help" />
      </button>
      {isVisible && (
        <div className="absolute left-0 top-full mt-1 z-50" style={{ minWidth: '200px' }}>
          <div className="relative bg-gray-900 text-white text-xs rounded-lg shadow-xl p-3 whitespace-normal">
            {text}
            <div className="absolute bottom-full left-4 w-0 h-0 border-l-4 border-r-4 border-b-4 border-transparent border-b-gray-900"></div>
          </div>
        </div>
      )}
    </div>
  );
}