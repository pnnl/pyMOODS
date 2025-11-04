import React, { useState } from 'react';

interface VerticalSliderProps {
  min?: number;
  max?: number;
  step?: number;
  onChange?: (value: number) => void;
}

const VerticalSlider: React.FC<VerticalSliderProps> = ({
  min = 0,
  max = 1,
  step = 0.1,
  onChange,
}) => {
  const [value, setValue] = useState<number>((min + max) / 2);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = parseFloat(e.target.value);
    setValue(newValue);
    onChange?.(newValue);
  };

  return (
    <div style={styles.container}>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={handleChange}
        className="clean-vertical-slider"
      />
      <div style={styles.valueLabel}>{value.toFixed(1)}</div>

      <style>{`
        .clean-vertical-slider {
          writing-mode: bt-lr;
          -webkit-appearance: slider-vertical;
          appearance: slider-vertical;
          height: 100%;
          width: 28px;
          background: transparent;
          margin: 0;
          padding: 0;
        }

        .clean-vertical-slider::-webkit-slider-thumb {
          -webkit-appearance: none;
          height: 16px;
          width: 16px;
          border-radius: 50%;
          background: transparent;
          border: 2px solid #3f51b5;
          box-shadow: 0 0 1px rgba(0, 0, 0, 0.2);
          margin-left: -6px;
          cursor: pointer;
        }

        .clean-vertical-slider::-webkit-slider-thumb:hover {
          background: #f0f0f0;
        }

        .clean-vertical-slider::-webkit-slider-runnable-track {
          width: 4px;
          background: #e0e0e0;
          border-radius: 2px;
        }

        .clean-vertical-slider::-moz-range-thumb {
          height: 16px;
          width: 16px;
          border-radius: 50%;
          background: transparent;
          border: 2px solid #3f51b5;
          cursor: pointer;
        }

        .clean-vertical-slider::-moz-range-thumb:hover {
          background: #f0f0f0;
        }

        .clean-vertical-slider::-moz-range-track {
          width: 4px;
          background: #e0e0e0;
          border-radius: 2px;
        }
      `}</style>
    </div>
  );
};

const styles: { [key: string]: React.CSSProperties } = {
  container: {
    height: '100%',
    width: '60px',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'space-between',
    fontFamily: 'Inter, Roboto, sans-serif',
    padding: '10px 0',
  },
  valueLabel: {
    marginTop: '10px',
    fontSize: '13px',
    fontWeight: 500,
    color: '#3f3f3f',
  },
};

export default VerticalSlider;
