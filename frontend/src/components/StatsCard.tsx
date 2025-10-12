import React from 'react';
import { StatsCardProps } from '../types';

const StatsCard: React.FC<StatsCardProps> = ({ title, value, icon, color = 'primary' }) => {
  return (
    <div className={`stats-card stats-card-${color}`}>
      {icon && <div className="stats-icon">{icon}</div>}
      <div className="stats-content">
        <h4 className="stats-title">{title}</h4>
        <p className="stats-value">{value}</p>
      </div>
    </div>
  );
};

export default StatsCard;
