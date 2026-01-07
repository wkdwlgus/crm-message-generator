import React, { useState } from 'react';
import BeautyProfileSelector from '../beautyprofile/BeautyProfileSelector';
import { HistoryFeed } from '../history/HistoryFeed';

export const CustomerDashboard = () => {
  const [activeTab, setActiveTab] = useState<'PROFILE' | 'HISTORY'>('PROFILE');

  const tabBaseStyle = "flex-1 py-3 text-center font-black text-xs uppercase tracking-widest transition-colors border-b-2 border-black cursor-pointer";
  const activeStyle = "bg-black text-white";
  const inactiveStyle = "bg-white text-gray-400 hover:text-black hover:bg-gray-50";

  return (
    <div className="flex flex-col h-full">
      {/* 탭 헤더 */}
      <div className="flex mb-6">
        <button
          onClick={() => setActiveTab('PROFILE')}
          className={`${tabBaseStyle} ${activeTab === 'PROFILE' ? activeStyle : inactiveStyle}`}
        >
          ⚙️ Profile Settings
        </button>
        <div className="w-0.5 bg-black"></div>
        <button
          onClick={() => setActiveTab('HISTORY')}
          className={`${tabBaseStyle} ${activeTab === 'HISTORY' ? activeStyle : inactiveStyle}`}
        >
          🕒 Message History
        </button>
      </div>

      {/* 탭 컨텐츠 영역 */}
      <div className="min-h-[400px]">
        {activeTab === 'PROFILE' ? (
          <div className="animate-in fade-in slide-in-from-bottom-2 duration-200">
             {/* 기존 컴포넌트 렌더링 */}
            <BeautyProfileSelector />
          </div>
        ) : (
          <div className="animate-in fade-in slide-in-from-bottom-2 duration-200">
            <HistoryFeed />
          </div>
        )}
      </div>
    </div>
  );
};