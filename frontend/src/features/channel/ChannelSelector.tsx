import React, { useState } from 'react';
import { useAppStore } from '../../store/useAppStore';
import type { ChannelType } from '../../store/useAppStore';

type Props = {
  embedded?: boolean; 
};

export function ChannelSelector({ embedded = false }: Props) {
  const { selectedChannel, setSelectedChannel } = useAppStore();
  const [hoveredId, setHoveredId] = useState<string | null>(null);

  const channels: { id: ChannelType; label: string; icon: string; desc: string }[] = [
    { id: 'APP_PUSH', label: 'APP PUSH', icon: '📱', desc: '앱 사용자에게 무료로 발송되는 푸시 알림입니다.' },
    { id: 'SMS', label: 'SMS / MMS', icon: '💬', desc: '도달율이 높은 문자 메시지입니다. 비용이 발생할 수 있습니다.' },
    { id: 'KAKAO', label: 'KAKAO TALK', icon: '💛', desc: '카카오 알림톡/친구톡으로 발송됩니다. 이미지 활용에 좋습니다.' },
    { id: 'EMAIL', label: 'E-MAIL', icon: '📧', desc: '상세한 내용을 담을 수 있는 뉴스레터 형식입니다.' },
  ];

  const Content = (
    <>
      <label className="block text-xs font-black uppercase mb-4 tracking-wider text-gray-700">
        📮 CHOOSE DELIVERY METHOD (발송 채널 선택)
      </label>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {channels.map((ch) => {
          const isSelected = selectedChannel === ch.id;

          return (
            <div key={ch.id} className="relative group">
              <button
                onClick={() => setSelectedChannel(isSelected ? null : ch.id)}
                onMouseEnter={() => setHoveredId(ch.id)}
                onMouseLeave={() => setHoveredId(null)}
                className={`
                  w-full py-6 px-4 border-2 border-black transition-all duration-200 flex flex-col items-center gap-3
                  ${isSelected
                    ? 'bg-yellow-300 shadow-none translate-x-[2px] translate-y-[2px]'
                    : 'bg-white shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] hover:bg-gray-50'
                  }
                `}
              >
                <span className="text-3xl filter drop-shadow-sm">{ch.icon}</span>
                <span className="font-black text-sm tracking-tight">{ch.label}</span>
              </button>

              {hoveredId === ch.id && (
                <div className="absolute bottom-full mb-3 left-1/2 -translate-x-1/2 w-48 z-20 bg-black text-white text-xs p-2 text-center animate-fadeIn shadow-xl pointer-events-none">
                  {ch.desc}
                  <div className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-2 h-2 bg-black rotate-45"></div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </>
  );

  if (!embedded) {
    return (
      <section className="mb-10">
        <h2 className="font-black text-2xl mb-6 border-b-4 border-black inline-block italic pr-4">
          3. SELECT CHANNEL
        </h2>

        <div className="p-6 border-2 border-black bg-white shadow-[8px_8px_0px_0px_rgba(0,0,0,1)]">
          {Content}
        </div>
      </section>
    );
  }

  return <div className="pt-6">{Content}</div>;
}

export default ChannelSelector;